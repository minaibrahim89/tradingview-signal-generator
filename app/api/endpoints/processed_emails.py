from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.models.database import get_db, ProcessedEmail

router = APIRouter()


class ProcessedEmailResponse(BaseModel):
    """Processed email response model"""
    id: int
    message_id: str
    sender: str
    subject: str
    received_at: datetime
    processed_at: datetime
    forwarded_successfully: bool
    body_snippet: Optional[str] = None

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    data: List[ProcessedEmailResponse]
    total: int
    page: int
    page_size: int


@router.get("/", response_model=PaginatedResponse)
async def get_processed_emails(
    page: int = Query(0, ge=0),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    search: Optional[str] = None,
    days: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get processed emails with filtering and pagination"""
    query = db.query(ProcessedEmail)

    # Filter by status if provided
    if status:
        if status.lower() == "success":
            query = query.filter(ProcessedEmail.forwarded_successfully == True)
        elif status.lower() == "failed":
            query = query.filter(
                ProcessedEmail.forwarded_successfully == False)

    # Filter by date if days provided
    if days:
        from_date = datetime.now() - timedelta(days=days)
        query = query.filter(ProcessedEmail.processed_at >= from_date)

    # Filter by search term if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                ProcessedEmail.subject.ilike(search_term),
                ProcessedEmail.sender.ilike(search_term),
                ProcessedEmail.body_snippet.ilike(search_term)
            )
        )

    # Get total count for pagination
    total = query.count()

    # Apply ordering and pagination
    query = query.order_by(desc(ProcessedEmail.processed_at))
    query = query.offset(page * page_size).limit(page_size)

    # Execute query
    emails = query.all()

    return {
        "data": emails,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{email_id}", response_model=ProcessedEmailResponse)
async def get_processed_email(email_id: int, db: Session = Depends(get_db)):
    """Get a specific processed email by ID"""
    email = db.query(ProcessedEmail).filter(
        ProcessedEmail.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email


@router.delete("/{email_id}")
async def delete_processed_email(email_id: int, db: Session = Depends(get_db)):
    """Delete a processed email record"""
    email = db.query(ProcessedEmail).filter(
        ProcessedEmail.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    db.delete(email)
    db.commit()

    return {"status": "success", "message": "Email record deleted successfully"}


@router.delete("/")
async def clear_all_processed_emails(db: Session = Depends(get_db)):
    """Clear all processed email records"""
    # Get count before deletion for reporting
    count = db.query(ProcessedEmail).count()
    
    # Delete all records
    db.query(ProcessedEmail).delete()
    db.commit()
    
    return {
        "status": "success", 
        "message": f"Successfully cleared {count} processed email records"
    }


@router.delete("", status_code=200)
async def clear_all_processed_emails_no_slash(db: Session = Depends(get_db)):
    """Clear all processed email records (endpoint without trailing slash)"""
    return await clear_all_processed_emails(db)
