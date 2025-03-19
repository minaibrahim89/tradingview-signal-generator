from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Dict, List, Any
from datetime import datetime, timedelta

from app.models.database import get_db, EmailMonitorConfig, WebhookConfig, ProcessedEmail

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get stats for the dashboard"""

    # Count active webhooks
    active_webhooks_count = db.query(func.count(WebhookConfig.id)).filter(
        WebhookConfig.active == True).scalar() or 0

    # Count active email configs
    active_configs_count = db.query(func.count(EmailMonitorConfig.id)).filter(
        EmailMonitorConfig.active == True).scalar() or 0

    # Count total processed emails
    total_emails = db.query(func.count(ProcessedEmail.id)).scalar() or 0

    # Count successfully processed emails
    success_emails = db.query(func.count(ProcessedEmail.id)).filter(
        ProcessedEmail.forwarded_successfully == True).scalar() or 0

    # Count emails processed in the last 24 hours
    last_24h = datetime.now() - timedelta(days=1)
    emails_24h = db.query(func.count(ProcessedEmail.id)).filter(
        ProcessedEmail.processed_at >= last_24h).scalar() or 0

    # Get recent emails (last 5)
    recent_emails = db.query(ProcessedEmail).order_by(
        desc(ProcessedEmail.processed_at)).limit(5).all()

    # Calculate success rate
    success_rate = 0
    if total_emails > 0:
        success_rate = (success_emails / total_emails) * 100

    return {
        "active_webhooks": active_webhooks_count,
        "active_email_configs": active_configs_count,
        "total_emails_processed": total_emails,
        "emails_processed_24h": emails_24h,
        "success_rate": success_rate,
        "recent_emails": recent_emails
    }


@router.get("/processed-emails/summary")
async def get_processed_emails_summary(db: Session = Depends(get_db)):
    """Get summary of processed emails"""

    # Total emails processed
    total = db.query(func.count(ProcessedEmail.id)).scalar() or 0

    # Total successfully forwarded
    success = db.query(func.count(ProcessedEmail.id)).filter(
        ProcessedEmail.forwarded_successfully == True).scalar() or 0

    # Total failed
    failed = total - success

    # Group by date (last 7 days)
    last_7_days = datetime.now() - timedelta(days=7)

    daily_stats = []
    for i in range(7):
        day = datetime.now() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59,
                              second=59, microsecond=999999)

        count = db.query(func.count(ProcessedEmail.id)).filter(
            ProcessedEmail.processed_at >= day_start,
            ProcessedEmail.processed_at <= day_end
        ).scalar() or 0

        daily_stats.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "count": count
        })

    return {
        "total_emails": total,
        "successful_emails": success,
        "failed_emails": failed,
        "success_rate": (success / total * 100) if total > 0 else 0,
        "daily_stats": daily_stats
    }
