import os
import base64
import json
import logging

logger = logging.getLogger(__name__)

def get_google_credentials_data():
    """
    Loads Google API credentials from either:
    1. GOOGLE_CREDENTIALS_BASE64 environment variable (recommended for production)
    2. credentials.json file (fallback)
    
    Returns:
        dict: The credentials data as a dictionary
        None: If credentials couldn't be loaded
    """
    # Check if credentials are available as base64 in environment variable
    credentials_base64 = os.environ.get('GOOGLE_CREDENTIALS_BASE64')
    
    if credentials_base64:
        try:
            # Decode base64 string to JSON
            logger.info("Loading credentials from environment variable")
            credentials_json = base64.b64decode(credentials_base64).decode('utf-8')
            return json.loads(credentials_json)
        except Exception as e:
            logger.error(f"Failed to load credentials from environment variable: {e}")
            print(f"ERROR: Failed to load credentials from environment variable: {e}")
            # Don't return yet, try the file method as fallback
    
    # Fallback to file-based credentials
    credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
    logger.info(f"Looking for credentials file at: {credentials_path}")
    
    if not os.path.exists(credentials_path):
        logger.error(f"Credentials file not found at: {credentials_path}")
        return None
    
    try:
        with open(credentials_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load credentials from file: {e}")
        print(f"ERROR: Failed to load credentials from file: {e}")
        return None

def save_credentials_to_token_file(credentials, token_path):
    """
    Save credentials to token file.
    
    Args:
        credentials: Google OAuth credentials object
        token_path: Path to save token file
    """
    # Create credentials info dictionary
    creds_data = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes,
    }
    
    # Add id_token if available (contains user info including email)
    if hasattr(credentials, 'id_token'):
        creds_data['id_token'] = credentials.id_token
    
    # Extract email from id_token if available
    if hasattr(credentials, 'id_token') and credentials.id_token:
        try:
            # Parse JWT payload (second part of the token)
            jwt_segments = credentials.id_token.split('.')
            if len(jwt_segments) >= 2:
                payload = jwt_segments[1]
                # Add padding if needed
                payload += '=' * (4 - len(payload) % 4) if len(payload) % 4 else ''
                # Decode base64
                decoded = base64.b64decode(payload).decode('utf-8')
                token_data = json.loads(decoded)
                if 'email' in token_data:
                    creds_data['email'] = token_data['email']
        except Exception as e:
            logger.error(f"Error extracting email from id_token: {e}")
    
    # Save to file
    try:
        os.makedirs(os.path.dirname(os.path.abspath(token_path)), exist_ok=True)
        with open(token_path, 'w') as token_file:
            json.dump(creds_data, token_file)
        logger.info(f"Credentials saved to {token_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving credentials to {token_path}: {e}")
        return False 