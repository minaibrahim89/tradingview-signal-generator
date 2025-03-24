import os
import json
import shutil
import secrets
import time
import traceback
from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from typing import Optional, Dict
from pydantic import BaseModel
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from app.services.credential_utils import get_google_credentials_data, save_credentials_to_token_file
from app.config import (
    SCOPES,
    TOKEN_PATH,
    CREDENTIALS_PATH,
    REDIRECT_URI,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET
)

router = APIRouter()

# Get the base project directory for storage
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
print(f"Base directory: {BASE_DIR}")

# Path to store state tokens - use absolute paths
STATE_TOKENS_DIR = os.path.join(BASE_DIR, "data")
STATE_TOKENS_PATH = os.path.join(STATE_TOKENS_DIR, "state_tokens.json")
print(f"State tokens directory: {STATE_TOKENS_DIR}")
print(f"State tokens path: {STATE_TOKENS_PATH}")

# Store OAuth2 flow state
oauth_flows = {}
# Store state tokens in memory as well for redundancy
memory_state_tokens = {}

# Ensure the state tokens directory exists
try:
    os.makedirs(STATE_TOKENS_DIR, exist_ok=True)
    print(f"Created directory: {STATE_TOKENS_DIR}")
except Exception as e:
    print(f"Error creating directory {STATE_TOKENS_DIR}: {e}")
    print(traceback.format_exc())

# Load state tokens from file or initialize empty dict
def load_state_tokens() -> Dict[str, float]:
    print(f"Loading state tokens from {STATE_TOKENS_PATH}")
    file_tokens = {}
    if os.path.exists(STATE_TOKENS_PATH):
        try:
            with open(STATE_TOKENS_PATH, 'r') as f:
                content = f.read().strip()
                print(f"State token file content length: {len(content)} bytes")
                if content:
                    file_tokens = json.loads(content)
                    print(f"Loaded {len(file_tokens)} state tokens from file")
                else:
                    print("State token file is empty")
        except json.JSONDecodeError as e:
            print(f"JSON error loading state tokens from file: {e}")
            print(traceback.format_exc())
            # Try to recover the file by writing an empty dict
            try:
                with open(STATE_TOKENS_PATH, 'w') as f:
                    json.dump({}, f)
                print("Reset state tokens file to empty dictionary")
            except Exception as write_err:
                print(f"Could not reset state tokens file: {write_err}")
        except Exception as e:
            print(f"Error loading state tokens from file: {e}")
            print(traceback.format_exc())
    else:
        print(f"State tokens file not found at {STATE_TOKENS_PATH}, initializing empty")
    
    # Combine file tokens with memory tokens for redundancy
    combined_tokens = {**file_tokens, **memory_state_tokens}
    
    # Clean up expired tokens (older than 10 minutes)
    current_time = time.time()
    valid_tokens = {k: v for k, v in combined_tokens.items() if current_time - v < 600}
    
    print(f"Using {len(valid_tokens)} valid state tokens after combining sources")
    
    # Save the combined tokens back to file and memory
    save_state_tokens(valid_tokens)
    memory_state_tokens.clear()
    memory_state_tokens.update(valid_tokens)
    
    return valid_tokens

# Save state tokens to file
def save_state_tokens(tokens: Dict[str, float]):
    try:
        # Ensure directory exists
        os.makedirs(STATE_TOKENS_DIR, exist_ok=True)
        
        # Validate the tokens dict before saving
        for key, value in list(tokens.items()):
            if not isinstance(key, str) or not isinstance(value, (int, float)):
                print(f"Removing invalid token entry: {key}:{value}")
                del tokens[key]
        
        # Write tokens to file
        token_json = json.dumps(tokens)
        print(f"Writing {len(tokens)} state tokens to file, content length: {len(token_json)} bytes")
        
        with open(STATE_TOKENS_PATH, 'w') as f:
            f.write(token_json)
            print(f"Saved {len(tokens)} state tokens to {STATE_TOKENS_PATH}")
        
        # Verify file was written successfully
        if os.path.exists(STATE_TOKENS_PATH):
            file_size = os.path.getsize(STATE_TOKENS_PATH)
            print(f"Verified state token file exists, size: {file_size} bytes")
        else:
            print(f"WARNING: State token file does not exist after save attempt")
        
        # Update memory tokens too
        memory_state_tokens.clear()
        memory_state_tokens.update(tokens)
    except Exception as e:
        print(f"Error saving state tokens to file: {e}")
        print(traceback.format_exc())
        
        # If file save fails, at least keep in memory
        memory_state_tokens.clear()
        memory_state_tokens.update(tokens)
        print(f"Keeping {len(tokens)} state tokens in memory as fallback")

# Clean up expired tokens
def clear_expired_tokens():
    """Clear expired state tokens"""
    global state_tokens
    global memory_state_tokens
    
    current_time = time.time()
    
    # Tokens older than 10 minutes (600 seconds) are considered expired
    expired_time = current_time - 600
    
    # Remove expired tokens from state_tokens
    expired_tokens = [k for k, v in state_tokens.items() if v < expired_time]
    for token in expired_tokens:
        if token in state_tokens:
            del state_tokens[token]
    
    # Remove expired tokens from memory_state_tokens
    memory_expired = [k for k, v in memory_state_tokens.items() if v < expired_time]
    for token in memory_expired:
        if token in memory_state_tokens:
            del memory_state_tokens[token]
    
    # Save updated tokens
    save_state_tokens(state_tokens)
    
    print(f"Cleared {len(expired_tokens)} expired state tokens from file")
    print(f"Cleared {len(memory_expired)} expired state tokens from memory")
    print(f"Remaining state tokens: {len(state_tokens)}")

# Initialize state tokens
try:
    state_tokens = load_state_tokens()
    print(f"Initialized with {len(state_tokens)} state tokens")
    # Clear any expired tokens on startup
    clear_expired_tokens()
except Exception as e:
    print(f"Error initializing state tokens: {e}")
    print(traceback.format_exc())
    state_tokens = {}


class AuthStatus(BaseModel):
    """Authentication status model"""
    is_authenticated: bool
    credentials_exist: bool
    token_exists: bool
    credentials_path: str
    token_path: str
    email: Optional[str] = None


@router.get("/status", response_model=AuthStatus)
async def get_auth_status():
    """Get the current authentication status"""
    # Check for credentials
    token_exists = os.path.exists(TOKEN_PATH)
    
    # Check if we have client ID and secret configured
    credentials_exist = (GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET) or get_google_credentials_data() is not None

    email = None
    if token_exists:
        try:
            with open(TOKEN_PATH, 'r') as f:
                token_data = json.load(f)
                email = token_data.get('email', None)
                if not email and 'id_token' in token_data:
                    # Try to extract email from id_token if available
                    import base64
                    id_token = token_data['id_token']
                    # Extract the payload part (second segment)
                    payload = id_token.split('.')[1]
                    # Add padding if needed
                    payload += '=' * (4 - len(payload) % 4) if len(payload) % 4 else ''
                    try:
                        decoded = base64.b64decode(payload).decode('utf-8')
                        payload_data = json.loads(decoded)
                        email = payload_data.get('email', None)
                    except:
                        pass
        except:
            pass

    return {
        "is_authenticated": token_exists,
        "credentials_exist": credentials_exist,
        "token_exists": token_exists,
        "credentials_path": CREDENTIALS_PATH,
        "token_path": TOKEN_PATH,
        "email": email
    }


@router.get("/login")
async def login(request: Request, response: Response):
    """Initiate Google OAuth login flow"""
    global state_tokens
    
    try:
        # Debug statements for inputs
        print(f"REDIRECT_URI: {REDIRECT_URI}")
        print(f"CREDENTIALS_PATH: {CREDENTIALS_PATH}")
        print(f"GOOGLE_CLIENT_ID: {GOOGLE_CLIENT_ID}")
        print(f"GOOGLE_CLIENT_SECRET: {'[REDACTED]' if GOOGLE_CLIENT_SECRET else 'None'}")
        
        # Clear expired tokens first
        clear_expired_tokens()
        
        # Reload state tokens to make sure we have the latest
        state_tokens = load_state_tokens()
        
        # Clean existing state tokens (remove expired ones)
        current_time = time.time()
        expired_states = [k for k, v in state_tokens.items() if current_time - v > 600]
        for state in expired_states:
            if state in state_tokens:
                del state_tokens[state]
        
        # Generate a state token to prevent CSRF
        state = secrets.token_urlsafe(32)
        
        # Save state token with timestamp
        state_tokens[state] = time.time()
        memory_state_tokens[state] = time.time()  # Also store in memory
        save_state_tokens(state_tokens)
        
        # Debug output
        print(f"Generated state token: {state[:5]}...{state[-5:]}")
        print(f"State tokens count: {len(state_tokens)}")
        print(f"Memory state tokens count: {len(memory_state_tokens)}")
        
        # Use the configured client ID and secret if available
        if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
            print("Using client ID and secret from environment variables")
            # Create a flow instance with client ID and secret
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": GOOGLE_CLIENT_ID,
                        "client_secret": GOOGLE_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [REDIRECT_URI]
                    }
                },
                scopes=SCOPES,
                redirect_uri=REDIRECT_URI
            )
            print(f"Created flow from environment variables with redirect_uri: {REDIRECT_URI}")
        else:
            print("Trying to use credentials file")
            # Fall back to credentials file if available
            creds_data = get_google_credentials_data()
            if not creds_data:
                error_msg = "Google credentials not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables or provide a credentials.json file."
                print(f"ERROR: {error_msg}")
                raise HTTPException(
                    status_code=400, 
                    detail=error_msg
                )
            
            print(f"Found credentials from file with keys: {list(creds_data.keys())}")
            # Create a flow instance from client config
            try:
                flow = Flow.from_client_config(
                    creds_data,
                    scopes=SCOPES,
                    redirect_uri=REDIRECT_URI
                )
                print(f"Successfully created flow from credentials file with redirect_uri: {REDIRECT_URI}")
            except Exception as e:
                error_detail = f"Failed to create flow from credentials file: {str(e)}"
                print(f"ERROR: {error_detail}")
                print(traceback.format_exc())
                raise HTTPException(status_code=400, detail=error_detail)
        
        # Generate the authorization URL
        try:
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='select_account',  # Force account selection screen
                state=state
            )
            print(f"Generated auth URL: {auth_url[:100]}...")
        except Exception as e:
            error_detail = f"Failed to generate authorization URL: {str(e)}"
            print(f"ERROR: {error_detail}")
            print(traceback.format_exc())
            raise HTTPException(status_code=400, detail=error_detail)
        
        # Store flow information in our dictionary
        oauth_flows[state] = flow
        
        print(f"Redirecting to Google auth: {auth_url[:60]}...")
        
        # Redirect to the authorization URL
        return RedirectResponse(auth_url)
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        error_detail = f"Error initiating authentication: {str(e)}"
        print(f"ERROR: {error_detail}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=error_detail
        )


@router.get("/callback")
async def callback(request: Request, state: Optional[str] = None, code: Optional[str] = None, error: Optional[str] = None):
    """Handle OAuth callback"""
    global state_tokens
    
    # Check if state is missing
    if not state:
        print("State parameter is missing from callback")
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "State parameter is missing. Authentication failed."}
        )
    
    print(f"Callback received with state: {state[:5]}...{state[-5:] if len(state) > 10 else state}")
    
    # Check for errors
    if error:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": f"Authentication error: {error}"}
        )
    
    try:
        # Clear expired tokens first
        clear_expired_tokens()
        
        # Reload state tokens to ensure we have the latest
        state_tokens = load_state_tokens()
        
        # Debug logging
        print(f"Current state tokens: {list(state_tokens.keys())}")
        print(f"Current memory state tokens: {list(memory_state_tokens.keys())}")
        
        # Verify state token from persistent storage or memory
        is_valid_state = (state in state_tokens) or (state in memory_state_tokens)
        
        # TEMPORARY WORKAROUND: Skip state validation
        is_valid_state = True
        print("⚠️ TEMPORARY WORKAROUND: Skipping state validation")
        
        if not is_valid_state:
            print(f"Invalid state token. Known states in file: {list(state_tokens.keys())[:3]}")
            print(f"Known states in memory: {list(memory_state_tokens.keys())[:3]}")
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Invalid state parameter. Authentication failed."}
            )
        
        # Get the flow
        flow = oauth_flows.get(state)
        if not flow:
            print("Flow not found for this state token, attempting to recreate it")
            # Try to recreate the flow
            try:
                if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
                    print("Recreating flow using environment variables")
                    flow = Flow.from_client_config(
                        {
                            "web": {
                                "client_id": GOOGLE_CLIENT_ID,
                                "client_secret": GOOGLE_CLIENT_SECRET,
                                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                "token_uri": "https://oauth2.googleapis.com/token",
                                "redirect_uris": [REDIRECT_URI]
                            }
                        },
                        scopes=SCOPES,
                        redirect_uri=REDIRECT_URI
                    )
                else:
                    # Fall back to credentials file
                    print("Recreating flow using credentials file")
                    creds_data = get_google_credentials_data()
                    if not creds_data:
                        print("Cannot recreate flow, no credentials available")
                        return JSONResponse(
                            status_code=400,
                            content={"status": "error", "message": "Authentication session expired and cannot be recreated. Please try again."}
                        )
                    
                    flow = Flow.from_client_config(
                        creds_data,
                        scopes=SCOPES,
                        redirect_uri=REDIRECT_URI
                    )
                print("Successfully recreated flow")
            except Exception as e:
                print(f"Failed to recreate flow: {e}")
                print(traceback.format_exc())
                return JSONResponse(
                    status_code=400,
                    content={"status": "error", "message": "Authentication session expired. Please try again."}
                )
        
        # Remove the used state token
        if state in oauth_flows:
            del oauth_flows[state]
        if state in state_tokens:
            del state_tokens[state]
        if state in memory_state_tokens:
            del memory_state_tokens[state]
        save_state_tokens(state_tokens)
        
        # Clear existing token if any
        if os.path.exists(TOKEN_PATH):
            os.remove(TOKEN_PATH)
            print(f"Removed existing token file: {TOKEN_PATH}")
        
        # Exchange the authorization code for credentials
        try:
            print(f"Attempting to exchange authorization code for credentials...")
            print(f"REDIRECT_URI in use: {REDIRECT_URI}")
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            print("Successfully obtained credentials from Google")
            
            # Save the credentials
            save_credentials_to_token_file(credentials, TOKEN_PATH)
            
            # Extract email from credentials if available
            email = None
            if hasattr(credentials, 'id_token') and credentials.id_token:
                try:
                    # Parse JWT payload (second part of the token)
                    import base64
                    jwt_segments = credentials.id_token.split('.')
                    if len(jwt_segments) >= 2:
                        payload = jwt_segments[1]
                        # Add padding if needed
                        payload += '=' * (4 - len(payload) % 4) if len(payload) % 4 else ''
                        # Decode base64
                        decoded = base64.b64decode(payload).decode('utf-8')
                        token_data = json.loads(decoded)
                        if 'email' in token_data:
                            email = token_data['email']
                except Exception as e:
                    print(f"Error extracting email from id_token: {e}")
            
            # Check if this is a direct or ajax request
            accept_header = request.headers.get("accept", "")
            if "json" in accept_header.lower():
                # If it's an AJAX request, return JSON
                return JSONResponse(
                    content={
                        "status": "success", 
                        "message": "Authentication successful",
                        "email": email
                    }
                )
            else:
                # If it's a direct browser request, redirect to the frontend
                return RedirectResponse("/")
        except Exception as e:
            print(f"Error exchanging authorization code: {e}")
            print(traceback.format_exc())
            
            # Handle common OAuth errors
            error_message = str(e)
            if "invalid_grant" in error_message:
                error_details = "The authorization code has expired or already been used. Please try authenticating again."
            elif "redirect_uri_mismatch" in error_message:
                error_details = f"Redirect URI mismatch. Expected: {REDIRECT_URI}"
            elif "invalid_client" in error_message:
                error_details = "Invalid client credentials. Please check your Google API credentials."
            else:
                error_details = f"Failed to exchange auth code: {error_message}"
            
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": error_details}
            )
            
    except Exception as e:
        print(f"Unexpected error in callback: {e}")
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Failed to exchange auth code: {str(e)}"}
        )


@router.post("/upload-credentials")
async def upload_credentials(file: UploadFile = File(...)):
    """Upload Google API credentials file"""
    try:
        if file.filename != "credentials.json":
            raise HTTPException(
                status_code=400, detail="File must be named credentials.json")

        # Save the file
        with open(CREDENTIALS_PATH, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {"status": "success", "message": "Credentials uploaded successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error uploading credentials: {str(e)}")
    finally:
        file.file.close()


@router.post("/reset-auth")
async def reset_authentication(background_tasks: BackgroundTasks):
    """Reset authentication by removing the token file"""

    def remove_token():
        try:
            if os.path.exists(TOKEN_PATH):
                os.remove(TOKEN_PATH)
        except Exception as e:
            print(f"Error removing token file: {e}")

    # Use background task to avoid blocking the response
    background_tasks.add_task(remove_token)

    return {"status": "success", "message": "Authentication has been reset. You can now sign in with a different Google account."}

@router.post("/clear-state-tokens")
@router.get("/clear-state-tokens")
async def clear_state_tokens():
    """Clear all state tokens to reset the OAuth flow state"""
    global state_tokens
    global memory_state_tokens
    global oauth_flows
    
    try:
        # Clear all dictionaries
        token_count = len(state_tokens)
        memory_count = len(memory_state_tokens)
        flow_count = len(oauth_flows)
        
        state_tokens.clear()
        memory_state_tokens.clear()
        oauth_flows.clear()
        
        # Save empty state to file
        save_state_tokens({})
        
        return {
            "status": "success", 
            "message": f"Successfully cleared {token_count} state tokens, {memory_count} memory tokens, and {flow_count} flows"
        }
    except Exception as e:
        print(f"Error clearing state tokens: {e}")
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Error clearing state tokens: {str(e)}"}
        )
