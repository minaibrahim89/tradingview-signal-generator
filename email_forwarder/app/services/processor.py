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

    async def initialize_gmail_service(self):
        """Initialize the Gmail API service."""
        try:
            # Check if token exists
            credentials = None
            token_path = os.getenv("GMAIL_TOKEN_PATH", "token.json")
            credentials_path = os.getenv(
                "GMAIL_CREDENTIALS_PATH", "credentials.json")

            logger.info(f"Looking for token at: {token_path}")
            logger.info(f"Looking for credentials at: {credentials_path}")

            # First, check if credentials file exists
            if not os.path.exists(credentials_path):
                logger.error(
                    f"Credentials file not found at {credentials_path}")
                print(
                    f"\nERROR: Credentials file not found at {credentials_path}")
                print("\nPlease download OAuth credentials from Google Cloud Console:")
                print("1. Go to https://console.cloud.google.com/")
                print("2. Select your project")
                print("3. Go to APIs & Services > Credentials")
                print("4. Create or download existing OAuth client ID credentials")
                print(
                    "5. Save the file as 'credentials.json' in the application directory")
                return False

            if os.path.exists(token_path):
                logger.info("Found existing token.json, loading credentials")
                try:
                    with open(token_path, 'r') as token_file:
                        token_data = json.load(token_file)
                    credentials = Credentials.from_authorized_user_info(
                        token_data, SCOPES)
                except Exception as e:
                    logger.error(f"Error loading token file: {e}")
                    credentials = None
                    # Remove corrupted token file
                    if os.path.exists(token_path):
                        os.remove(token_path)
                        logger.info(
                            f"Removed corrupted token file: {token_path}")

            # If no valid credentials available, let the user log in
            if not credentials or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    logger.info("Refreshing expired credentials")
                    try:
                        credentials.refresh(Request())
                    except Exception as e:
                        logger.error(f"Error refreshing credentials: {e}")
                        credentials = None
                        # Remove invalid token
                        if os.path.exists(token_path):
                            os.remove(token_path)
                            logger.info(
                                f"Removed invalid token file: {token_path}")

                if not credentials:
                    # Load the OAuth client ID file
                    try:
                        with open(credentials_path, 'r') as f:
                            client_info = json.load(f)

                        # Verify it's a desktop client type
                        if 'installed' not in client_info:
                            logger.error(
                                "Invalid credentials.json: Not a desktop app client type")
                            print(
                                "\nERROR: Your credentials.json file is not for a desktop application.")
                            print(
                                "Please create OAuth credentials with application type 'Desktop app'.")
                            return False
                    except Exception as e:
                        logger.error(f"Error reading credentials file: {e}")
                        print(f"\nERROR: Could not read credentials file: {e}")
                        return False

                    logger.info("Starting OAuth flow for user consent")

                    try:
                        # Configure flow with specific settings to avoid errors
                        flow = InstalledAppFlow.from_client_secrets_file(
                            credentials_path, SCOPES)

                        # Set redirect URI
                        flow.redirect_uri = "http://localhost"

                        # Check if we're in a headless environment
                        use_local_server = os.getenv(
                            "USE_LOCAL_SERVER_AUTH", "false").lower() == "true"

                        if use_local_server:
                            logger.info(
                                "Using local server authentication flow")
                            try:
                                credentials = flow.run_local_server(port=0)
                            except Exception as e:
                                logger.error(
                                    f"Error in local server auth: {e}")
                                print(
                                    f"\nError during local server authentication: {e}")
                                print("Falling back to manual authorization...")
                                use_local_server = False

                        if not use_local_server:
                            # Console-based auth for headless environments
                            logger.info("Using manual authorization flow")

                            # Generate authorization URL with specific parameters
                            auth_url, _ = flow.authorization_url(
                                access_type='offline',
                                include_granted_scopes='true',
                                prompt='consent'
                            )

                            print("\n")
                            print("=" * 80)
                            print("IMPORTANT: AUTHORIZATION REQUIRED")
                            print("=" * 80)
                            print(
                                "\nPlease open this URL in your browser and sign in with your Gmail account:")
                            print(f"\n{auth_url}\n")
                            print("IMPORTANT INSTRUCTIONS:")
                            print("1. When prompted, click 'Continue' to proceed")
                            print(
                                "2. Select your Google account that has the emails you want to monitor")
                            print(
                                "3. You may see a warning that says 'Google hasn't verified this app'")
                            print(
                                "   → Click 'Continue' or 'Advanced' and then 'Go to <your project> (unsafe)'")
                            print(
                                "4. On the consent screen, click 'ALLOW' to grant access to your Gmail")
                            print(
                                "5. You will be redirected to localhost (which may show as not working - that's normal)")
                            print(
                                "6. From the browser address bar, copy the ENTIRE URL after redirection")
                            print("=" * 80)

                            # Get the redirected URL from user
                            redirect_url = input(
                                "\nPaste the full redirect URL here: ").strip()

                            # Extract code from redirect URL if user pasted the full URL
                            if redirect_url.startswith("http://localhost") and "?code=" in redirect_url:
                                try:
                                    from urllib.parse import parse_qs, urlparse
                                    parsed_url = urlparse(redirect_url)
                                    auth_code = parse_qs(parsed_url.query)[
                                        'code'][0]
                                    logger.info(
                                        "Successfully extracted code from redirect URL")
                                except Exception as e:
                                    logger.error(
                                        f"Error extracting code from URL: {e}")
                                    auth_code = input(
                                        "Could not extract code. Please enter just the code part: ").strip()
                            else:
                                auth_code = redirect_url  # Assume user entered just the code

                            try:
                                # Exchange auth code for credentials
                                logger.info(
                                    f"Exchanging authorization code for credentials")
                                flow.fetch_token(code=auth_code)
                                credentials = flow.credentials
                                logger.info(
                                    "Successfully obtained credentials")
                            except Exception as e:
                                logger.error(
                                    f"Error exchanging auth code: {e}")
                                print(
                                    f"\nError exchanging authorization code: {e}")

                                if "access_denied" in str(e).lower():
                                    print(
                                        "\nACCESS DENIED ERROR: You must click ALLOW on the consent screen.")
                                    print(
                                        "Please try again and make sure to grant permission when prompted.")
                                elif "invalid_grant" in str(e).lower():
                                    print(
                                        "\nINVALID GRANT ERROR: The authorization code is invalid or expired.")
                                    print(
                                        "Please try again with a fresh authorization URL.")

                                return False
                    except Exception as e:
                        logger.error(f"Error in OAuth flow: {e}")
                        print(f"\nError in OAuth flow: {e}")
                        print("\nTroubleshooting steps:")
                        print(
                            "1. Make sure your credentials.json is for a Desktop application")
                        print(
                            "2. Verify that your Google Cloud project has the Gmail API enabled")
                        print(
                            "3. Check that your OAuth consent screen is configured correctly")
                        print("4. Ensure you have added yourself as a test user")
                        print(
                            "5. When authorizing, make sure to click 'ALLOW' on the consent screen")
                        print(
                            "6. If you see 'This app isn't verified', click Advanced and then 'Go to <project> (unsafe)'")
                        return False

                # Save the credentials for the next run
                if credentials:
                    logger.info(f"Saving credentials to {token_path}")
                    try:
                        with open(token_path, 'w') as token:
                            token.write(credentials.to_json())
                        logger.info("Credentials saved successfully")
                    except Exception as e:
                        logger.error(f"Error saving credentials: {e}")
                        print(f"Warning: Could not save credentials: {e}")

            # Build the Gmail service
            self._service = build('gmail', 'v1', credentials=credentials)
            logger.info("Gmail service initialized successfully")
            print("\nSuccessfully authenticated with Gmail!")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Gmail service: {e}")
            print(f"\nError initializing Gmail service: {e}")
            return False

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
            # Build query for Gmail API
            query = f"to:{config.email_address}"
            if config.filter_sender:
                query += f" from:{config.filter_sender}"
            if config.filter_subject:
                query += f" subject:{config.filter_subject}"

            # Only get recent messages (last 24 hours)
            time_filter = (datetime.now() - timedelta(days=1)
                           ).strftime('%Y/%m/%d')
            query += f" after:{time_filter}"

            # Execute the query
            results = self._service.users().messages().list(userId='me', q=query).execute()
            messages = results.get('messages', [])

            for message in messages:
                message_id = message['id']

                # Check if we've already processed this message
                async with self._lock:
                    if message_id in self._processed_ids:
                        continue

                # Check database for already processed
                existing = db.query(ProcessedEmail).filter(
                    ProcessedEmail.message_id == message_id).first()
                if existing:
                    self._processed_ids.add(message_id)
                    continue

                # Get the message content
                msg = self._service.users().messages().get(
                    userId='me', id=message_id).execute()

                # Extract headers
                headers = {h['name']: h['value']
                           for h in msg['payload']['headers']}
                sender = headers.get('From', '')
                subject = headers.get('Subject', '')
                date_str = headers.get('Date', '')

                # Try to parse the date
                received_at = datetime.now()
                try:
                    from email.utils import parsedate_to_datetime
                    received_at = parsedate_to_datetime(date_str)
                except:
                    pass

                # Extract body
                body = self._get_email_body(msg)

                if not body:
                    logger.warning(
                        f"Could not extract body from email {message_id}")
                    continue

                # Forward to webhooks
                success = await self._forward_to_webhooks(body, subject, sender, db)

                # Record this email as processed
                processed = ProcessedEmail(
                    message_id=message_id,
                    sender=sender,
                    subject=subject,
                    received_at=received_at,
                    forwarded_successfully=success,
                    body_snippet=body[:500] if body else None
                )
                db.add(processed)
                db.commit()

                # Add to in-memory set
                self._processed_ids.add(message_id)

                logger.info(f"Processed email: {subject} from {sender}")

        except Exception as e:
            logger.error(f"Error checking emails: {e}")

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
                    # Set headers with the webhook's content type
                    headers = {"Content-Type": webhook.content_type}
                    
                    # Determine if we should send just the raw body or the JSON payload
                    if webhook.send_raw_body:
                        # Send just the raw email body
                        async with session.post(
                            webhook.url,
                            data=body,
                            headers=headers
                        ) as response:
                            if response.status < 300:
                                logger.info(f"Successfully forwarded email to webhook: {webhook.name}")
                                success = True
                            else:
                                text = await response.text()
                                logger.error(f"Failed to forward email to webhook {webhook.name}: Status {response.status}, Response: {text}")
                    else:
                        # Send structured JSON payload
                        async with session.post(
                            webhook.url,
                            json=payload,
                            headers=headers
                        ) as response:
                            if response.status < 300:
                                logger.info(f"Successfully forwarded email to webhook: {webhook.name}")
                                success = True
                            else:
                                text = await response.text()
                                logger.error(f"Failed to forward email to webhook {webhook.name}: Status {response.status}, Response: {text}")
                except Exception as e:
                    logger.error(
                        f"Error sending to webhook {webhook.name}: {e}")

        return success
