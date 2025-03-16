import asyncio
import os
import sys
import platform
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.gzip import GZipMiddleware
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session

from app.api.endpoints import router as api_router
from app.models.database import get_db, initialize_db
from app.services.processor import EmailProcessor

load_dotenv()

# Initialize processor
email_processor = EmailProcessor()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database
    initialize_db()

    # Get a database session
    db_generator = get_db()
    db = next(db_generator)

    # Start the background task
    task = await email_processor.start_background_tasks(db)
    if task is None:
        print(
            "WARNING: Email processor failed to start. Gmail monitoring will not be active.")
        print("Please check your Gmail API credentials and permissions.")

    yield

    # Stop the background task
    email_processor.stop_monitoring()
    try:
        db_generator.close()
    except:
        pass


app = FastAPI(
    title="Email Signal Forwarder",
    description="""
    An application that monitors Gmail for trading signals and forwards them to webhooks.
    
    ## Features
    
    * Monitor Gmail inbox for new emails
    * Filter emails by sender, subject, etc.
    * Forward email content to configurable webhooks
    * Track processed emails to avoid duplicates
    
    ## Setup
    
    1. Configure Gmail API credentials
    2. Add webhook targets
    3. Add email monitoring configurations
    """,
    version="1.0.0",
    lifespan=lifespan,
    # Redirect trailing slashes - this will handle both /webhooks and /webhooks/
    redirect_slashes=True
)

# Define allowed origins for CORS
# In development, the React app runs on port 5173 by default
origins = [
    "http://localhost:5173",    # Vite dev server
    "http://localhost:8000",    # FastAPI server
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
]

# CORS setup with expanded settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "Content-Length", "Content-Disposition"],
)

# Add GZip compression for responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Debug: Print registered routers before inclusion
print("="*80)
print("API ROUTER ROUTES BEFORE INCLUSION:")
for route in api_router.routes:
    if hasattr(route, "path"):
        print(f"Route: {route.path}")
print("="*80)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Debug: Print all app routes after inclusion
print("="*80)
print("ALL APP ROUTES AFTER INCLUSION:")
for route in app.routes:
    if hasattr(route, "path"):
        print(f"Route: {route.path}")
print("="*80)

# Serve static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Add a test endpoint to verify API connectivity
@app.get("/api/test", include_in_schema=False)
async def test_api():
    """Test endpoint to verify API connectivity"""
    return JSONResponse(content={"status": "ok", "message": "API is working correctly"})


@app.get("/health")
async def health_check():
    """Enhanced health check endpoint for monitoring."""
    # Get system info
    python_version = sys.version.split()[0]
    os_info = f"{platform.system()} {platform.release()}"

    token_path = os.getenv("GMAIL_TOKEN_PATH", "token.json")
    credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")

    return {
        "status": "ok",
        "version": "1.0.0",
        "environment": {
            "python_version": python_version,
            "os": os_info
        },
        "email_processor_active": email_processor._running,
        "auth_status": {
            "token_exists": os.path.exists(token_path),
            "credentials_exist": os.path.exists(credentials_path)
        }
    }


# Serve frontend
@app.get("/{full_path:path}")
async def serve_frontend(request: Request, full_path: str):
    """Serve the frontend React app."""
    # Check if the path is an API call - already handled by the API router
    # But in case someone tries to access /api/* directly without the /api/v1 prefix
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route not found")

    # Serve the index.html for all other paths
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        # If frontend is not built yet, redirect to API docs
        return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"

    print(f"Starting server on http://{host}:{port}")
    print(f"Debug mode: {debug}")
    print(f"Documentation: http://{host}:{port}/docs")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug
    )
