from fastapi import APIRouter
from app.api.endpoints import webhooks, email_configs

router = APIRouter()

router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
router.include_router(email_configs.router,
                      prefix="/email-configs", tags=["email-configs"])
