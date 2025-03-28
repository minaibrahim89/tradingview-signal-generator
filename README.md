# Gmail Signal Forwarder

This application monitors a Gmail account for specific emails and forwards their content to configured webhooks.

## Features

- Monitor Gmail inbox for new emails
- Filter emails by sender, subject, or other criteria
- Forward email content to configurable webhooks
- Track processed emails to avoid duplicates
- Web-based dashboard to manage configuration

## Setup

### Prerequisites

- Python 3.9 or higher
- Node.js 16 or higher
- pnpm (for frontend development)
- Google Cloud account

### Installation

1. Clone the repository
   ```
   git clone https://github.com/yourusername/gmail-signal-forwarder.git
   cd gmail-signal-forwarder
   ```

2. Set up a virtual environment
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Install frontend dependencies
   ```
   cd frontend
   pnpm install
   ```

4. Build the frontend
   ```
   pnpm build
   ```

5. Create a `.env` file in the root directory with your configuration
   ```
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback
   ```

### Google OAuth Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Navigate to "APIs & Services" > "Library"
4. Search for and enable the "Gmail API"
5. Go to "APIs & Services" > "Credentials"
6. Click "Create Credentials" > "OAuth client ID"
7. Select "Web application" as the application type
8. Add an authorized redirect URI: `http://localhost:8000/api/v1/auth/callback`
9. Download the credentials JSON file
10. Use the credentials to set up the application in one of these ways:
    - Save as `credentials.json` in the root directory of the application
    - Set the environment variables in your `.env` file:
      ```
      GOOGLE_CLIENT_ID=your_client_id
      GOOGLE_CLIENT_SECRET=your_client_secret
      ```

### Running the Application

1. Start the application
   ```
   python main.py
   ```

2. Open your browser and navigate to `http://localhost:8000`

3. Click "Sign in with Google" to authenticate with your Gmail account

## Setting Up Google Authentication

To connect the application to a Google account, you need to:

1. **Create a Google Cloud Project and OAuth credentials**:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Navigate to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Web application" as the application type
   - Name your OAuth client
   - Add authorized redirect URIs:
     - For local development: `http://localhost:5173/auth/callback`
     - For production: `https://yourapp.com/auth/callback`
   - Click "Create"
   - Download the credentials JSON file

2. **Add the credentials to your application**:
   - Save the downloaded JSON file as `credentials.json` in the `app/` directory
   - Alternatively, set the environment variables `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in your `.env` file

3. **Enable the Gmail API**:
   - In the Google Cloud Console, navigate to "APIs & Services" > "Library"
   - Search for "Gmail API" and enable it for your project

4. **Test the authentication**:
   - Start your application (frontend and backend)
   - Navigate to the Settings page
   - Click "Sign in with Google"
   - Follow the authentication flow
   - After successful authentication, you should be redirected back to your application

5. **Troubleshooting**:
   - If you encounter "redirect_uri_mismatch" errors, ensure your redirect URI exactly matches what's configured in the Google Cloud Console
   - For "invalid_grant" errors, try clearing OAuth state tokens in the Advanced Settings section
   - Check that your credentials.json file is properly formatted and located in the app/ directory

## Usage

1. Set up webhooks in the Webhooks section
2. Configure email monitoring in the Email Configs section
3. The application will check for new emails and forward them to the configured webhooks

## Development

### Backend

The backend is built with FastAPI. To run it in development mode:

```
python -m uvicorn main:app --reload
```

### Frontend

The frontend is built with React and Material-UI. To run it in development mode:

```
cd frontend
pnpm dev
```

## Environment Variables

- `GOOGLE_CLIENT_ID`: Your Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Your Google OAuth client secret
- `GOOGLE_REDIRECT_URI`: The OAuth redirect URI (default: http://localhost:8000/api/v1/auth/callback)
- `PORT`: The port to run the application on (default: 8000)
- `GMAIL_TOKEN_PATH`: Path to store the OAuth token (default: token.json)
- `GMAIL_CREDENTIALS_PATH`: Path to the credentials file (default: credentials.json)
- `SECRET_KEY`: Secret key for session cookies (automatically generated if not provided)

## License

MIT
