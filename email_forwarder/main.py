import asyncio
import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
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
    lifespan=lifespan
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Redirect to API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "email_processor_active": email_processor._running
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug
    )
