import os
import base64
import json
import logging
from google.oauth2.credentials import Credentials

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
    try:
        # Check for credentials.json
        script_dir = os.path.dirname(os.path.abspath(__file__))
        app_dir = os.path.dirname(script_dir)  # Go up one level to app directory
        credentials_path = os.path.join(app_dir, "credentials.json")
        
        logger.info(f"Looking for credentials file at: {credentials_path}")
        
        if os.path.exists(credentials_path):
            with open(credentials_path, 'r') as f:
                return json.load(f)
        else:
            logger.warning(f"Credentials file not found at: {credentials_path}")
            return None
    except Exception as e:
        logger.error(f"Error reading credentials: {e}")
        return None

def save_credentials_to_token_file(credentials, token_path):
    """
    Save credentials to token file.
    
    Args:
        credentials: Google OAuth credentials object
        token_path: Path to save token file
    """
    try:
        print(f"Starting to save credentials to token file: {token_path}")
        
        # Check if path is empty or None
        if not token_path or token_path.strip() == '':
            # Use a fallback path in case token_path is empty
            print("ERROR: Token path is empty! Using fallback path.")
            import os
            script_dir = os.path.dirname(os.path.abspath(__file__))
            app_dir = os.path.dirname(script_dir)  # app directory
            token_path = os.path.join(app_dir, "token.json")
            print(f"Using fallback token path: {token_path}")
        
        # Ensure directory exists
        token_dir = os.path.dirname(token_path)
        print(f"Token directory path: '{token_dir}'")
        
        # Check if token_dir is empty
        if not token_dir or token_dir.strip() == '':
            print("WARNING: Token directory is empty, using current directory")
            token_dir = os.path.dirname(os.path.abspath(__file__))
            token_path = os.path.join(token_dir, "token.json")
            print(f"Using directory {token_dir} and updated token_path to {token_path}")
            
        try:
            print(f"Creating directory {token_dir}")
            os.makedirs(token_dir, exist_ok=True)
            print(f"Directory created successfully: {os.path.exists(token_dir)}")
            print(f"Directory writable: {os.access(token_dir, os.W_OK)}")
        except Exception as dir_error:
            print(f"ERROR creating directory {token_dir}: {dir_error}")
            # If we can't create the directory, try using the current directory
            import os
            current_dir = os.getcwd()
            print(f"Falling back to current directory: {current_dir}")
            token_path = os.path.join(current_dir, "token.json")
            print(f"New token path: {token_path}")
        
        # Debug information
        print(f"Saving credentials to token path: {token_path}")
        print(f"Token path directory exists: {os.path.exists(os.path.dirname(token_path))}")
        print(f"Credential attributes: {dir(credentials)}")
        
        # Create a dictionary with all required fields for token refresh
        token_data = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
        }
        
        # Add extra fields if available
        if hasattr(credentials, 'id_token'):
            token_data['id_token'] = credentials.id_token
        
        if hasattr(credentials, 'expiry'):
            token_data['expiry'] = credentials.expiry.isoformat() if credentials.expiry else None
            
        # Add email from payload if available
        if hasattr(credentials, 'id_token') and credentials.id_token:
            try:
                jwt_segments = credentials.id_token.split('.')
                if len(jwt_segments) >= 2:
                    payload = jwt_segments[1]
                    # Add padding if needed
                    payload += '=' * (4 - len(payload) % 4) if len(payload) % 4 else ''
                    # Decode base64
                    decoded = base64.b64decode(payload).decode('utf-8')
                    token_data_jwt = json.loads(decoded)
                    if 'email' in token_data_jwt:
                        token_data['email'] = token_data_jwt['email']
                        print(f"Extracted email from token: {token_data_jwt['email']}")
            except Exception as e:
                print(f"Error extracting email from id_token: {e}")
                logger.error(f"Error extracting email from id_token: {e}")
        
        # Write the token data to file
        token_json = json.dumps(token_data)
        print(f"Writing token data (length: {len(token_json)}) to {token_path}")
        
        try:
            with open(token_path, 'w') as f:
                print(f"File opened for writing: {token_path}")
                json.dump(token_data, f)
                print(f"Data written to file: {token_path}")
        except Exception as write_error:
            print(f"ERROR writing token file: {write_error}")
            logger.error(f"Error writing token file: {write_error}")
            
            # Try one more time with a different approach
            try:
                print("Trying alternative approach to write file")
                with open(token_path, 'w', encoding='utf-8') as f:
                    f.write(token_json)
                print("Alternative write approach succeeded")
            except Exception as alt_write_error:
                print(f"Alternative write approach also failed: {alt_write_error}")
                return False
            
        # Verify the token file was created with all required fields
        if not os.path.exists(token_path):
            print(f"ERROR: Failed to create token file at {token_path}")
            logger.error(f"Failed to create token file at {token_path}")
            return False
        
        # Verify token contains all required fields
        try:
            with open(token_path, 'r') as f:
                saved_token = json.load(f)
                missing_fields = []
                for required_field in ['refresh_token', 'token_uri', 'client_id', 'client_secret']:
                    if required_field not in saved_token or not saved_token[required_field]:
                        missing_fields.append(required_field)
                
                if missing_fields:
                    print(f"WARNING: Token file is missing required fields: {', '.join(missing_fields)}")
                    logger.error(f"Token file is missing required fields: {', '.join(missing_fields)}")
                    return False
                
                print(f"Successfully verified token file has all required fields")
        except Exception as verify_error:
            print(f"ERROR verifying token file: {verify_error}")
            # If we can't verify, still consider it a success if the file exists
            
        return True
    except Exception as e:
        print(f"ERROR: Failed to save credentials to token file: {e}")
        logger.error(f"Error saving credentials to token file: {e}")
        import traceback
        print(traceback.format_exc())
        return False 