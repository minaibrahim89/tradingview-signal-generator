import os
import json
import shutil
from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional
from pydantic import BaseModel

router = APIRouter()

# Paths
TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH", "token.json")
CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")


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
    credentials_exist = os.path.exists(CREDENTIALS_PATH)
    token_exists = os.path.exists(TOKEN_PATH)

    email = None
    if token_exists:
        try:
            with open(TOKEN_PATH, 'r') as f:
                token_data = json.load(f)
                email = token_data.get('email', None)
                if not email and 'id_token' in token_data:
                    # Try to extract email from id_token if available
                    import base64
                    import json
                    id_token = token_data['id_token']
                    # Extract the payload part (second segment)
                    payload = id_token.split('.')[1]
                    # Add padding if needed
                    payload += '=' * (4 - len(payload) %
                                      4) if len(payload) % 4 else ''
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

    return {"status": "success", "message": "Authentication will be reset. Please restart the application to re-authenticate."}
