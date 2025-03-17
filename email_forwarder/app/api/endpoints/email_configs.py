from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.models.database import EmailMonitorConfig, get_db
from app.schemas.email_config import EmailMonitorCreate, EmailMonitorUpdate, EmailMonitorInDB

router = APIRouter()


@router.post("/", response_model=EmailMonitorInDB, status_code=status.HTTP_201_CREATED)
def create_email_config(config: EmailMonitorCreate, db: Session = Depends(get_db)):
    """Create a new email monitor configuration."""
    # Convert empty strings to None
    data = config.dict()
    if "filter_subject" in data and data["filter_subject"] == "":
        data["filter_subject"] = None
    if "filter_sender" in data and data["filter_sender"] == "":
        data["filter_sender"] = None
        
    db_config = EmailMonitorConfig(**data)
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


@router.get("/", response_model=List[EmailMonitorInDB])
def get_email_configs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all email monitor configurations."""
    configs = db.query(EmailMonitorConfig).offset(skip).limit(limit).all()
    return configs


@router.get("", response_model=List[EmailMonitorInDB])
def get_email_configs_no_slash(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all email monitor configurations (endpoint without trailing slash)."""
    return get_email_configs(skip, limit, db)


@router.get("/{config_id}", response_model=EmailMonitorInDB)
def get_email_config(config_id: int, db: Session = Depends(get_db)):
    """Get a specific email monitor configuration by ID."""
    config = db.query(EmailMonitorConfig).filter(
        EmailMonitorConfig.id == config_id).first()
    if config is None:
        raise HTTPException(
            status_code=404, detail="Email monitor configuration not found")
    return config


@router.get("/{config_id}/", response_model=EmailMonitorInDB)
def get_email_config_with_slash(config_id: int, db: Session = Depends(get_db)):
    """Get a specific email monitor configuration by ID (endpoint with trailing slash)."""
    return get_email_config(config_id, db)


@router.put("/{config_id}", response_model=EmailMonitorInDB)
def update_email_config(config_id: int, config: EmailMonitorUpdate, db: Session = Depends(get_db)):
    """Update an email monitor configuration."""
    db_config = db.query(EmailMonitorConfig).filter(
        EmailMonitorConfig.id == config_id).first()
    if db_config is None:
        raise HTTPException(
            status_code=404, detail="Email monitor configuration not found")

    update_data = config.dict(exclude_unset=True)
    # Convert empty strings to None
    if "filter_subject" in update_data and update_data["filter_subject"] == "":
        update_data["filter_subject"] = None
    if "filter_sender" in update_data and update_data["filter_sender"] == "":
        update_data["filter_sender"] = None
        
    for key, value in update_data.items():
        setattr(db_config, key, value)

    db.commit()
    db.refresh(db_config)
    return db_config


@router.put("/{config_id}/", response_model=EmailMonitorInDB)
def update_email_config_with_slash(config_id: int, config: EmailMonitorUpdate, db: Session = Depends(get_db)):
    """Update an email monitor configuration (endpoint with trailing slash)."""
    return update_email_config(config_id, config, db)


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_email_config(config_id: int, db: Session = Depends(get_db)):
    """Delete an email monitor configuration."""
    db_config = db.query(EmailMonitorConfig).filter(
        EmailMonitorConfig.id == config_id).first()
    if db_config is None:
        raise HTTPException(
            status_code=404, detail="Email monitor configuration not found")

    db.delete(db_config)
    db.commit()
    return None


@router.delete("/{config_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_email_config_with_slash(config_id: int, db: Session = Depends(get_db)):
    """Delete an email monitor configuration (endpoint with trailing slash)."""
    return delete_email_config(config_id, db)
