import asyncio
import os
import base64
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from sqlalchemy.orm import Session
import aiohttp
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from app.models.database import EmailMonitorConfig, WebhookConfig, ProcessedEmail
from app.api.endpoints.websocket import broadcast_email_processed
from app.services.credential_utils import get_google_credentials_data, save_credentials_to_token_file
from app.config import TOKEN_PATH, CREDENTIALS_PATH, SCOPES

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# For OAuth debugging during development only
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Allow HTTP for localhost
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'   # Allow scope downgrade


class EmailProcessor:
    def __init__(self):
        self._running = False
        self._tasks = set()
        self._processed_ids: Set[str] = set()
        self._lock = asyncio.Lock()
        self.credentials_path = CREDENTIALS_PATH
        self.token_path = TOKEN_PATH
        self._gmail_service = None
        
    async def initialize_gmail_service(self):
        """Initialize the Gmail API service."""
        try:
            credentials = await self._get_credentials()
            if not credentials:
                logger.error("Failed to get credentials. Gmail service not initialized.")
                return None
                
            # Build the Gmail API service
            logger.info("Building Gmail API service")
            self._gmail_service = build('gmail', 'v1', credentials=credentials)
            logger.info("Gmail API service initialized successfully")
            return self._gmail_service
        except Exception as e:
            logger.error(f"Error initializing Gmail service: {e}")
            return None
            
    async def _get_credentials(self):
        """Get OAuth2 credentials for the Gmail API."""
        try:
            logger.info(f"Looking for token at: {self.token_path}")
            
            # Load stored credentials token if it exists
            if os.path.exists(self.token_path):
                try:
                    credentials = self._load_token_file()
                    # Check if the credentials are valid or if they need to be refreshed
                    if credentials and credentials.expired and credentials.refresh_token:
                        logger.info("Refreshing expired credentials")
                        try:
                            credentials.refresh(Request())
                            # Save the refreshed credentials
                            save_credentials_to_token_file(credentials, self.token_path)
                        except Exception as refresh_error:
                            logger.error(f"Error refreshing credentials: {refresh_error}")
                            # Try the OAuth flow as a fallback
                            return None
                    return credentials
                except Exception as e:
                    logger.error(f"Error loading token file: {e}")
                    # Token file exists but is corrupted or invalid, remove it
                    if os.path.exists(self.token_path):
                        os.remove(self.token_path)
                        logger.info(f"Removed invalid token file: {self.token_path}")
                    return None
            
            # No valid token exists
            logger.warning("No valid token found. Authentication required.")
            logger.info("Please authenticate through the web interface at /api/v1/auth/login")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get credentials: {e}")
            return None
            
    def _load_token_file(self):
        """Load credentials from token file."""
        try:
            logger.info("Found existing token.json, loading credentials")
            with open(self.token_path, 'r') as token_file:
                token_data = json.load(token_file)
            return Credentials.from_authorized_user_info(token_data, SCOPES)
        except Exception as e:
            logger.error(f"Error loading token file: {e}")
            # Remove corrupted token file
            if os.path.exists(self.token_path):
                os.remove(self.token_path)
                logger.info(f"Removed corrupted token file: {self.token_path}")
            return None

    def _save_credentials(self, credentials):
        """Save credentials to token file."""
        try:
            save_credentials_to_token_file(credentials, self.token_path)
            return True
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
            return False
            
    async def start_background_tasks(self, db: Session):
        """Start all background tasks."""
        # First attempt to initialize the Gmail service
        self._gmail_service = await self.initialize_gmail_service()
        
        if not self._gmail_service:
            logger.warning("Gmail service not initialized. Monitoring tasks will not start.")
            return None
            
        logger.info("Starting email monitor tasks")
        self._running = True

        # Start the monitor task
        monitor_task = asyncio.create_task(self._email_monitor_loop(db))
        self._tasks.add(monitor_task)
        monitor_task.add_done_callback(self._tasks.discard)
        
        return monitor_task

    def stop_monitoring(self):
        """Stop all monitoring tasks."""
        self._running = False
        for task in self._tasks:
            task.cancel()

    async def _email_monitor_loop(self, db: Session):
        """Main loop for checking emails periodically."""
        while self._running:
            try:
                # Get all active email monitor configurations
                configs = db.query(EmailMonitorConfig).filter(
                    EmailMonitorConfig.active == True).all()

                for config in configs:
                    try:
                        await self._check_emails(config, db)
                    except Exception as e:
                        logger.error(
                            f"Error checking emails for {config.email_address}: {e}")

                # Sleep before next check
                await asyncio.sleep(min(config.check_interval_seconds for config in configs) if configs else 60)
            except Exception as e:
                logger.error(f"Error in email monitor loop: {e}")
                await asyncio.sleep(60)  # Sleep and retry on error

    async def _check_emails(self, config: EmailMonitorConfig, db: Session):
        """Check for new emails based on the configuration."""
        if not self._gmail_service:
            logger.error("Gmail service not initialized")
            return

        try:
            query = self._build_gmail_query(config)
            results = self._gmail_service.users().messages().list(userId='me', q=query).execute()
            messages = results.get('messages', [])

            for message in messages:
                await self._process_email_message(message, db)

        except Exception as e:
            logger.error(f"Error checking emails: {e}")

    def _build_gmail_query(self, config: EmailMonitorConfig) -> str:
        """Build Gmail API query string based on config."""
        query = f"to:{config.email_address}"
        if config.filter_sender:
            query += f" from:{config.filter_sender}"
        if config.filter_subject:
            query += f" subject:{config.filter_subject}"

        # Only get recent messages (last 24 hours)
        time_filter = (datetime.now() - timedelta(days=1)).strftime('%Y/%m/%d')
        query += f" after:{time_filter}"

        return query

    async def _process_email_message(self, message, db: Session):
        """Process a single email message."""
        message_id = message['id']

        # Check if we've already processed this message
        async with self._lock:
            if message_id in self._processed_ids:
                return

        # Check database for already processed
        existing = db.query(ProcessedEmail).filter(
            ProcessedEmail.message_id == message_id).first()
        if existing:
            self._processed_ids.add(message_id)
            return

        # Get the message content
        msg = self._gmail_service.users().messages().get(
            userId='me', id=message_id).execute()

        # Extract email data
        email_data = self._extract_email_data(msg)
        if not email_data.get('body'):
            logger.warning(f"Could not extract body from email {message_id}")
            return

        # Forward to webhooks
        success = await self._forward_to_webhooks(
            email_data['body'],
            email_data['subject'],
            email_data['sender'],
            db
        )

        # Record this email as processed
        processed = self._save_processed_email(
            message_id, email_data, success, db)

        # Add to in-memory set
        self._processed_ids.add(message_id)

        logger.info(
            f"Processed email: {email_data['subject']} from {email_data['sender']}")

        # Broadcast to WebSocket clients
        await self._broadcast_email_to_websocket(processed)

    def _extract_email_data(self, msg):
        """Extract data from an email message."""
        # Extract headers
        headers = {h['name']: h['value'] for h in msg['payload']['headers']}

        # Try to parse the date
        date_str = headers.get('Date', '')
        received_at = datetime.now()
        try:
            from email.utils import parsedate_to_datetime
            received_at = parsedate_to_datetime(date_str)
        except:
            pass

        return {
            'sender': headers.get('From', ''),
            'subject': headers.get('Subject', ''),
            'received_at': received_at,
            'body': self._get_email_body(msg)
        }

    def _save_processed_email(self, message_id, email_data, success, db):
        """Save a processed email record to the database."""
        processed = ProcessedEmail(
            message_id=message_id,
            sender=email_data['sender'],
            subject=email_data['subject'],
            received_at=email_data['received_at'],
            forwarded_successfully=success,
            body_snippet=email_data['body'][:500] if email_data['body'] else None
        )
        db.add(processed)
        db.commit()
        db.refresh(processed)
        return processed

    async def _broadcast_email_to_websocket(self, processed):
        """Broadcast processed email to WebSocket clients."""
        try:
            # Convert SQLAlchemy model to dict for WebSocket broadcast
            email_dict = {
                "id": processed.id,
                "message_id": processed.message_id,
                "sender": processed.sender,
                "subject": processed.subject,
                "received_at": processed.received_at.isoformat() if processed.received_at else None,
                "processed_at": processed.processed_at.isoformat() if processed.processed_at else None,
                "forwarded_successfully": processed.forwarded_successfully,
                "body_snippet": processed.body_snippet
            }

            # Create a task to broadcast the email
            broadcast_task = asyncio.create_task(
                broadcast_email_processed(email_dict))
            broadcast_task.add_done_callback(
                lambda _: asyncio.create_task(
                    self._log_broadcast_completion(broadcast_task, processed.subject))
            )

        except Exception as e:
            logger.error(f"Error scheduling WebSocket broadcast: {e}")

    async def _log_broadcast_completion(self, task, subject):
        """Log the completion of a WebSocket broadcast task."""
        try:
            await task
            logger.info(f"WebSocket broadcast completed for email: {subject}")
        except Exception as e:
            logger.error(f"WebSocket broadcast task failed: {e}")

    def _get_email_body(self, message):
        """Extract the body text from a Gmail message."""
        if 'payload' not in message:
            return None

        payload = message['payload']

        # Check for plain text parts first
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')

        # If no plain text, try the body directly
        if 'body' in payload and 'data' in payload['body']:
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')

        return None

    async def _forward_to_webhooks(self, body: str, subject: str, sender: str, db: Session) -> bool:
        """Forward the email content to all active webhooks."""
        webhooks = db.query(WebhookConfig).filter(
            WebhookConfig.active == True).all()

        if not webhooks:
            logger.warning("No active webhooks configured")
            return False

        payload = {
            "body": body,
            "subject": subject,
            "sender": sender,
            "timestamp": datetime.now().isoformat()
        }

        success = False

        async with aiohttp.ClientSession() as session:
            for webhook in webhooks:
                try:
                    success = await self._send_to_webhook(session, webhook, body, payload)
                except Exception as e:
                    logger.error(
                        f"Error sending to webhook {webhook.name}: {e}")

        return success

    async def _send_to_webhook(self, session, webhook, body, payload):
        """Send data to a single webhook."""
        headers = {"Content-Type": webhook.content_type}

        try:
            if webhook.send_raw_body:
                # Send just the raw email body
                async with session.post(webhook.url, data=body, headers=headers) as response:
                    return await self._process_webhook_response(response, webhook)
            else:
                # Send structured JSON payload
                async with session.post(webhook.url, json=payload, headers=headers) as response:
                    return await self._process_webhook_response(response, webhook)
        except Exception as e:
            logger.error(f"Error in webhook request to {webhook.name}: {e}")
            return False

    async def _process_webhook_response(self, response, webhook):
        """Process the response from a webhook request."""
        if response.status < 300:
            logger.info(
                f"Successfully forwarded email to webhook: {webhook.name}")
            return True
        else:
            text = await response.text()
            logger.error(
                f"Failed to forward email to webhook {webhook.name}: Status {response.status}, Response: {text}")
            return False
