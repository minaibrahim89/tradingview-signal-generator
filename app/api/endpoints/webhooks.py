from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import aiohttp
import json
from datetime import datetime

from app.models.database import WebhookConfig, get_db
from app.schemas.webhook import WebhookCreate, WebhookUpdate, WebhookInDB, TestWebhookResponse

router = APIRouter()


@router.post("/", response_model=WebhookInDB, status_code=status.HTTP_201_CREATED)
def create_webhook(webhook: WebhookCreate, db: Session = Depends(get_db)):
    """Create a new webhook configuration."""
    webhook_data = webhook.dict()
    # Convert URL to string to avoid SQLite type issues
    webhook_data["url"] = str(webhook_data["url"])
    db_webhook = WebhookConfig(**webhook_data)
    db.add(db_webhook)
    db.commit()
    db.refresh(db_webhook)
    return db_webhook


@router.get("/", response_model=List[WebhookInDB])
def get_webhooks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all webhook configurations."""
    webhooks = db.query(WebhookConfig).offset(skip).limit(limit).all()
    return webhooks


@router.get("", response_model=List[WebhookInDB])
def get_webhooks_no_slash(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all webhook configurations (endpoint without trailing slash)."""
    return get_webhooks(skip, limit, db)


@router.get("/{webhook_id}", response_model=WebhookInDB)
def get_webhook(webhook_id: int, db: Session = Depends(get_db)):
    """Get a specific webhook configuration by ID."""
    webhook = db.query(WebhookConfig).filter(
        WebhookConfig.id == webhook_id).first()
    if webhook is None:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return webhook


@router.put("/{webhook_id}", response_model=WebhookInDB)
def update_webhook(webhook_id: int, webhook: WebhookUpdate, db: Session = Depends(get_db)):
    """Update a webhook configuration."""
    db_webhook = db.query(WebhookConfig).filter(
        WebhookConfig.id == webhook_id).first()
    if db_webhook is None:
        raise HTTPException(status_code=404, detail="Webhook not found")

    update_data = webhook.dict(exclude_unset=True)
    # Convert URL to string if present
    if "url" in update_data:
        update_data["url"] = str(update_data["url"])
        
    for key, value in update_data.items():
        setattr(db_webhook, key, value)

    db.commit()
    db.refresh(db_webhook)
    return db_webhook


@router.put("/{webhook_id}/", response_model=WebhookInDB)
def update_webhook_with_slash(webhook_id: int, webhook: WebhookUpdate, db: Session = Depends(get_db)):
    """Update a webhook configuration (endpoint with trailing slash)."""
    return update_webhook(webhook_id, webhook, db)


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_webhook(webhook_id: int, db: Session = Depends(get_db)):
    """Delete a webhook configuration."""
    db_webhook = db.query(WebhookConfig).filter(
        WebhookConfig.id == webhook_id).first()
    if db_webhook is None:
        raise HTTPException(status_code=404, detail="Webhook not found")

    db.delete(db_webhook)
    db.commit()
    return None


@router.post("/{webhook_id}/test", response_model=TestWebhookResponse)
async def test_webhook(webhook_id: int, db: Session = Depends(get_db)):
    """Test a webhook by sending a sample email payload."""
    # Get the webhook
    webhook = db.query(WebhookConfig).filter(
        WebhookConfig.id == webhook_id).first()
    if webhook is None:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # Sample email body content
    email_body = "This is a test email body sent from the webhook testing feature."
    
    # Set headers based on content type
    headers = {"Content-Type": webhook.content_type}
    
    # Prepare the payload
    success = False
    status_code = None
    response_text = None
    sample_payload_str = ""
    
    try:
        async with aiohttp.ClientSession() as session:
            if webhook.send_raw_body:
                # Send just the raw email body
                data = email_body
                sample_payload_str = email_body
                async with session.post(
                    webhook.url,
                    data=data,
                    headers=headers
                ) as response:
                    status_code = response.status
                    response_text = await response.text()
                    success = status_code < 300
            else:
                # Send structured JSON payload
                json_payload = {
                    "body": email_body,
                    "subject": "Test Email for Webhook Configuration",
                    "sender": "test@example.com",
                    "timestamp": datetime.now().isoformat()
                }
                sample_payload_str = json.dumps(json_payload, indent=2)
                async with session.post(
                    webhook.url,
                    json=json_payload,
                    headers=headers
                ) as response:
                    status_code = response.status
                    response_text = await response.text()
                    success = status_code < 300
    except Exception as e:
        response_text = str(e)
    
    return {
        "success": success,
        "webhook_id": webhook_id,
        "webhook_name": webhook.name,
        "status_code": status_code,
        "response": response_text,
        "sample_payload": sample_payload_str
    }


@router.post("/{webhook_id}/test/", response_model=TestWebhookResponse)
async def test_webhook_with_slash(webhook_id: int, db: Session = Depends(get_db)):
    """Test a webhook by sending a sample email payload (endpoint with trailing slash)."""
    return await test_webhook(webhook_id, db)
