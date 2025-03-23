import os

# Authentication
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH", "token.json")
CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5173")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

# For local development only - DO NOT use in production
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = os.getenv('OAUTHLIB_INSECURE_TRANSPORT', '1') 