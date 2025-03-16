from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.models.database import WebhookConfig, get_db
from app.schemas.webhook import WebhookCreate, WebhookUpdate, WebhookInDB

router = APIRouter()


@router.post("/", response_model=WebhookInDB, status_code=status.HTTP_201_CREATED)
def create_webhook(webhook: WebhookCreate, db: Session = Depends(get_db)):
    """Create a new webhook configuration."""
    db_webhook = WebhookConfig(**webhook.dict())
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
    for key, value in update_data.items():
        setattr(db_webhook, key, value)

    db.commit()
    db.refresh(db_webhook)
    return db_webhook


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
