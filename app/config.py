import os

# Get the base project directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Authentication
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH", os.path.join(BASE_DIR, "token.json"))
CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", os.path.join(BASE_DIR, "credentials.json"))

# Make sure this matches the frontend route exactly
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5173/auth/callback")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

# For local development only - DO NOT use in production
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = os.getenv('OAUTHLIB_INSECURE_TRANSPORT', '1') 