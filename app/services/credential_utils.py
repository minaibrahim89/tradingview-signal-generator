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