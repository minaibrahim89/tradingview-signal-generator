import os

# Get the base project directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
print(f"Base directory in config.py: {BASE_DIR}")

# Authentication
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Fix for token path - ALWAYS save in app root directory
# Not in subdirectories like 'api'
token_fallback = os.path.normpath(os.path.join(BASE_DIR, "token.json"))
print(f"Initial token fallback path: {token_fallback}")

# If path is empty or invalid, use absolute path
if not token_fallback or token_fallback.strip() == '':
    print("WARNING: Generated token_fallback path is empty, using hardcoded fallback")
    # Explicitly use the app directory
    token_fallback = os.path.normpath(os.path.join(os.path.abspath(__file__), "../../app/token.json"))
    print(f"Using hardcoded app directory: {token_fallback}")

# Important: Get from env var or use the fallback
TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH", token_fallback)
if not TOKEN_PATH or not TOKEN_PATH.strip():
    print("WARNING: TOKEN_PATH is still empty after fallback, using absolute hardcoded path")
    # Last resort - use absolute path to app directory
    TOKEN_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "token.json"))

print(f"TOKEN_PATH set to: '{TOKEN_PATH}'")

CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", os.path.join(BASE_DIR, "credentials.json"))
print(f"CREDENTIALS_PATH set to: '{CREDENTIALS_PATH}'")

# Make sure this matches the frontend route exactly
# This should point to the React route, not the API endpoint
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5173/auth/callback")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

# For local development only - DO NOT use in production
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = os.getenv('OAUTHLIB_INSECURE_TRANSPORT', '1') 