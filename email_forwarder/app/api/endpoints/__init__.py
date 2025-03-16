from fastapi import APIRouter
from app.api.endpoints import webhooks, email_configs, processed_emails, stats, auth

router = APIRouter()

router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
router.include_router(email_configs.router,
                      prefix="/email-configs", tags=["email-configs"])
router.include_router(processed_emails.router,
                      prefix="/processed-emails", tags=["processed-emails"])
router.include_router(stats.router, prefix="/stats", tags=["stats"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
