# Gmail Trading Signal Forwarder

A Python FastAPI application that monitors Gmail inbox for trading signals and forwards them to configurable webhooks.

## Features

- Monitor Gmail inbox for new messages
- Filter emails by sender, subject, or other criteria
- Forward email body content to configurable webhook URLs
- Track processed emails to avoid duplicate processing
- RESTful API for configuration management
- SQLite database for persistent storage

## Requirements

- Python 3.8+
- Gmail account
- Google Cloud Platform account (for Gmail API access)

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd email_forwarder
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up Gmail API credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Gmail API for your project:

   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API" and enable it

4. Configure OAuth consent screen:

   - Go to "APIs & Services" > "OAuth consent screen"
   - Select "External" user type (or "Internal" if you have Google Workspace)
   - Fill in the required app information (app name, user support email, developer contact email)
   - Add the scope: `.../auth/gmail.readonly`
   - Add yourself as a test user by entering your Gmail address

5. Create OAuth 2.0 credentials:

   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" and select "OAuth client ID"
   - Application type: **Desktop app**
   - Name: Gmail Signal Forwarder (or your preferred name)

6. Download the credentials JSON file
7. Save the file as `credentials.json` in the application directory

### 5. Configure environment variables

Create a `.env` file in the application directory:

```
DEBUG=true
APP_HOST=0.0.0.0
APP_PORT=8000
DATABASE_URL=sqlite:///./email_forwarder.db
GMAIL_TOKEN_PATH=token.json
GMAIL_CREDENTIALS_PATH=credentials.json
# Set to "true" to use browser-based authentication (requires GUI)
# Set to "false" for headless environments (will show a URL to visit)
USE_LOCAL_SERVER_AUTH=false
```

## Running the application

```bash
python main.py
```

### Authentication methods

The application supports two authentication methods:

1. **Browser-based authentication** (Default in environments with GUI):

   - Set `USE_LOCAL_SERVER_AUTH=true` in your `.env` file
   - When you run the application, it will open a browser for you to authorize access to Gmail

2. **Headless authentication** (For servers without browsers):
   - Set `USE_LOCAL_SERVER_AUTH=false` in your `.env` file
   - When you run the application, it will display a URL in the console
   - Open that URL in a browser on any device
   - Complete the authorization in the browser
   - You will be redirected to a URL that starts with `http://localhost?code=`
   - Copy the **entire** value after `?code=` in the URL
   - Paste this code back in the console when prompted

### Troubleshooting OAuth errors

If you encounter an error like `Fehler 400: invalid_request` or other OAuth issues:

1. **Check your credentials.json**: Make sure you downloaded the correct credentials file for a **Desktop app** (not Web app)
2. **Verify project configuration**:
   - Ensure the Gmail API is enabled in your Google Cloud project
   - Check that your OAuth consent screen is properly configured
   - Make sure you've added yourself as a test user
3. **Clean up and retry**:
   - Delete any existing `token.json` file
   - Restart the application
   - When copying the authorization code, make sure to copy the entire code parameter from the URL
4. **Redirect URI**: If modifying the code, ensure your redirect URI matches what's configured in Google Cloud Console

## API Documentation

Once the application is running, you can access the API documentation at:

```
http://localhost:8000/docs
```

## Configuring the application

### 1. Add webhook endpoints

Use the `/api/v1/webhooks` endpoint to add URLs where email content should be forwarded.

Example:

```bash
curl -X POST "http://localhost:8000/api/v1/webhooks" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Trading Platform",
    "url": "https://your-trading-platform.com/webhook",
    "active": true
  }'
```

### 2. Configure email monitoring

Use the `/api/v1/email-configs` endpoint to configure which emails should be monitored.

Example:

```bash
curl -X POST "http://localhost:8000/api/v1/email-configs" \
  -H "Content-Type: application/json" \
  -d '{
    "email_address": "your-email@gmail.com",
    "filter_subject": "Trading Signal",
    "filter_sender": "signals@trading-provider.com",
    "check_interval_seconds": 60,
    "active": true
  }'
```

## Webhook Payload Format

When a matching email is received, the application will forward it to all active webhooks with the following JSON payload format:

```json
{
  "body": "The full email body content...",
  "subject": "Email subject",
  "sender": "sender@example.com",
  "timestamp": "2023-01-01T12:00:00.000Z"
}
```

## License

MIT
