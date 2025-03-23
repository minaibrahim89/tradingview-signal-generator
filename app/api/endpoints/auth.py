import os
import json
import shutil
import secrets
from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from typing import Optional
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

# Store OAuth2 flow state
oauth_flows = {}


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
    # Generate a state token to prevent CSRF
    state = secrets.token_urlsafe(32)
    
    # Use the configured client ID and secret if available
    if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
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
    else:
        # Fall back to credentials file if available
        creds_data = get_google_credentials_data()
        if not creds_data:
            raise HTTPException(
                status_code=400, 
                detail="Google credentials not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables."
            )
        
        # Create a flow instance from client config
        flow = Flow.from_client_config(
            creds_data,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
    
    # Generate the authorization URL
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
        state=state
    )
    
    # Store flow information in our dictionary
    oauth_flows[state] = flow
    
    # Redirect to the authorization URL
    return RedirectResponse(auth_url)


@router.get("/callback")
async def callback(request: Request, state: str, code: Optional[str] = None, error: Optional[str] = None):
    """Handle OAuth callback"""
    # Check for errors
    if error:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": f"Authentication error: {error}"}
        )
    
    # Verify state token
    if state not in oauth_flows:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Invalid state parameter. Authentication failed."}
        )
    
    # Get the flow
    flow = oauth_flows[state]
    
    # Remove the used state token
    del oauth_flows[state]
    
    try:
        # Exchange the authorization code for credentials
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Save the credentials
        save_credentials_to_token_file(credentials, TOKEN_PATH)
        
        # Redirect to the frontend
        return RedirectResponse("/")
    except Exception as e:
        return JSONResponse(
            status_code=400,
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
