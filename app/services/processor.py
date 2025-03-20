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
from app.services.credential_utils import get_google_credentials_data

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# For OAuth debugging
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Allow HTTP for localhost
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'   # Allow scope downgrade


class EmailProcessor:
    def __init__(self):
        self._running = False
        self._tasks = set()
        self._service = None
        self._processed_ids: Set[str] = set()
        self._lock = asyncio.Lock()
        self.token_path = os.getenv("GMAIL_TOKEN_PATH", "token.json")
        self.credentials_path = os.getenv(
            "GMAIL_CREDENTIALS_PATH", "credentials.json")

    async def initialize_gmail_service(self):
        """Initialize the Gmail API service."""
        try:
            credentials = await self._get_credentials()
            if not credentials:
                return False

            # Build the Gmail service
            self._service = build('gmail', 'v1', credentials=credentials)
            logger.info("Gmail service initialized successfully")
            print("\nSuccessfully authenticated with Gmail!")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Gmail service: {e}")
            print(f"\nError initializing Gmail service: {e}")
            return False

    async def _get_credentials(self):
        """Get Gmail API credentials through OAuth flow."""
        try:
            # Check if token exists
            credentials = None

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
                            self._save_credentials(credentials)
                        except Exception as refresh_error:
                            logger.error(f"Error refreshing credentials: {refresh_error}")
                            credentials = await self._handle_invalid_credentials(credentials)
                    return credentials
                except Exception as e:
                    logger.error(f"Error loading token file: {e}")
                    # Continue to the OAuth flow
            
            # If no valid token exists, perform OAuth flow
            # First, check if credentials can be loaded from environment or file
            
            creds_data = get_google_credentials_data()
            if not creds_data:
                self._show_credentials_error()
                return None
                
            # Verify it's a desktop client type
            installed = creds_data.get('installed', None)
            if not installed:
                logger.error("Invalid credentials: Not a desktop app client type")
                print("Invalid credentials.json: Not a desktop app client type")
                print("\nERROR: Your credentials.json file is not for a desktop application.")
                self._show_oauth_troubleshooting()
                return None
                
            # Perform the OAuth flow to get credentials
            return await self._perform_oauth_flow()
                
        except Exception as e:
            logger.error(f"Failed to get credentials: {e}")
            print(f"\nError getting credentials: {e}")
            return None
            
    def _show_credentials_error(self):
        """Show error message for missing credentials file."""
        print(
            f"\nERROR: Credentials file not found at {self.credentials_path}")
        print("\nPlease download OAuth credentials from Google Cloud Console:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Select your project")
        print("3. Go to APIs & Services > Credentials")
        print("4. Create or download existing OAuth client ID credentials")
        print("5. Save the file as 'credentials.json' in the application directory")

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

    async def _handle_invalid_credentials(self, credentials):
        """Handle expired or missing credentials."""
        # Try to refresh if expired
        if credentials and credentials.expired and credentials.refresh_token:
            try:
                logger.info("Refreshing expired credentials")
                credentials.refresh(Request())
                return credentials
            except Exception as e:
                logger.error(f"Error refreshing credentials: {e}")
                if os.path.exists(self.token_path):
                    os.remove(self.token_path)
                    logger.info(
                        f"Removed invalid token file: {self.token_path}")

        # Need to perform OAuth flow
        return await self._perform_oauth_flow()

    async def _perform_oauth_flow(self):
        """Perform the OAuth flow to get credentials."""
        try:
            creds_data = get_google_credentials_data()
            if not creds_data:
                return None
                
            # Create a flow using the credentials data
            flow = InstalledAppFlow.from_client_config(
                creds_data,
                scopes=['https://www.googleapis.com/auth/gmail.readonly']
            )
            
            # Rest of the method remains unchanged
            logger.info("Starting OAuth flow for user consent")

            # Configure flow with specific settings
            flow.redirect_uri = "http://localhost"

            # Determine authentication method
            use_local_server = os.getenv(
                "USE_LOCAL_SERVER_AUTH", "false").lower() == "true"

            if use_local_server:
                return self._run_local_server_auth(flow)
            else:
                return await self._run_manual_auth(flow)

        except Exception as e:
            logger.error(f"Error in OAuth flow: {e}")
            print(f"\nError in OAuth flow: {e}")
            self._show_oauth_troubleshooting()
            return None

    def _run_local_server_auth(self, flow):
        """Run the local server OAuth flow."""
        try:
            logger.info("Using local server authentication flow")
            return flow.run_local_server(port=0)
        except Exception as e:
            logger.error(f"Error in local server auth: {e}")
            print(f"\nError during local server authentication: {e}")
            print("Falling back to manual authorization...")
            return None

    async def _run_manual_auth(self, flow):
        """Run the manual OAuth flow."""
        logger.info("Using manual authorization flow")

        # Generate authorization URL
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )

        self._show_auth_instructions(auth_url)

        # Get the redirected URL from user
        redirect_url = input("\nPaste the full redirect URL here: ").strip()

        try:
            # Extract code from redirect URL
            auth_code = self._extract_auth_code(redirect_url)

            # Exchange auth code for credentials
            logger.info("Exchanging authorization code for credentials")
            flow.fetch_token(code=auth_code)
            credentials = flow.credentials
            logger.info("Successfully obtained credentials")
            return credentials
        except Exception as e:
            logger.error(f"Error exchanging auth code: {e}")
            print(f"\nError exchanging authorization code: {e}")
            self._show_auth_error_help(e)
            return None

    def _show_auth_instructions(self, auth_url):
        """Show instructions for the manual authorization flow."""
        print("\n")
        print("=" * 80)
        print("IMPORTANT: AUTHORIZATION REQUIRED")
        print("=" * 80)
        print("\nPlease open this URL in your browser and sign in with your Gmail account:")
        print(f"\n{auth_url}\n")
        print("IMPORTANT INSTRUCTIONS:")
        print("1. When prompted, click 'Continue' to proceed")
        print("2. Select your Google account that has the emails you want to monitor")
        print("3. You may see a warning that says 'Google hasn't verified this app'")
        print(
            "   → Click 'Continue' or 'Advanced' and then 'Go to <your project> (unsafe)'")
        print("4. On the consent screen, click 'ALLOW' to grant access to your Gmail")
        print("5. You will be redirected to localhost (which may show as not working - that's normal)")
        print("6. From the browser address bar, copy the ENTIRE URL after redirection")
        print("=" * 80)

    def _extract_auth_code(self, redirect_url):
        """Extract the authorization code from the redirect URL."""
        if redirect_url.startswith("http://localhost") and "?code=" in redirect_url:
            try:
                from urllib.parse import parse_qs, urlparse
                parsed_url = urlparse(redirect_url)
                auth_code = parse_qs(parsed_url.query)['code'][0]
                logger.info("Successfully extracted code from redirect URL")
                return auth_code
            except Exception as e:
                logger.error(f"Error extracting code from URL: {e}")
                return input("Could not extract code. Please enter just the code part: ").strip()
        else:
            return redirect_url  # Assume user entered just the code

    def _show_auth_error_help(self, error):
        """Show helpful messages for common auth errors."""
        if "access_denied" in str(error).lower():
            print("\nACCESS DENIED ERROR: You must click ALLOW on the consent screen.")
            print("Please try again and make sure to grant permission when prompted.")
        elif "invalid_grant" in str(error).lower():
            print("\nINVALID GRANT ERROR: The authorization code is invalid or expired.")
            print("Please try again with a fresh authorization URL.")

    def _show_oauth_troubleshooting(self):
        """Show troubleshooting steps for OAuth issues."""
        print("\nTroubleshooting steps:")
        print("1. Make sure your credentials.json is for a Desktop application")
        print("2. Verify that your Google Cloud project has the Gmail API enabled")
        print("3. Check that your OAuth consent screen is configured correctly")
        print("4. Ensure you have added yourself as a test user")
        print("5. When authorizing, make sure to click 'ALLOW' on the consent screen")
        print("6. If you see 'This app isn't verified', click Advanced and then 'Go to <project> (unsafe)'")

    def _save_credentials(self, credentials):
        """Save credentials to token file."""
        try:
            logger.info(f"Saving credentials to {self.token_path}")
            with open(self.token_path, 'w') as token:
                token.write(credentials.to_json())
            logger.info("Credentials saved successfully")
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
            print(f"Warning: Could not save credentials: {e}")

    async def start_background_tasks(self, db: Session):
        """Start background tasks for monitoring emails."""
        if self._running:
            return

        self._running = True

        # Initialize Gmail service
        success = await self.initialize_gmail_service()
        if not success:
            logger.error(
                "Failed to start email monitoring due to Gmail service initialization failure")
            self._running = False
            return None

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
        if not self._service:
            logger.error("Gmail service not initialized")
            return

        try:
            query = self._build_gmail_query(config)
            results = self._service.users().messages().list(userId='me', q=query).execute()
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
        msg = self._service.users().messages().get(
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
