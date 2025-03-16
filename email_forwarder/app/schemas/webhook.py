from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Any
from datetime import datetime


class WebhookBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100,
                      description="Name of the webhook configuration")
    url: HttpUrl = Field(..., description="URL to forward email content to")
    active: bool = Field(True, description="Whether this webhook is active")


class WebhookCreate(WebhookBase):
    pass


class WebhookUpdate(BaseModel):
    name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Name of the webhook configuration")
    url: Optional[HttpUrl] = Field(
        None, description="URL to forward email content to")
    active: Optional[bool] = Field(
        None, description="Whether this webhook is active")


class WebhookInDB(WebhookBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestWebhookResponse(BaseModel):
    success: bool = Field(..., description="Whether the test was successful")
    webhook_id: int = Field(..., description="ID of the tested webhook")
    webhook_name: str = Field(..., description="Name of the tested webhook")
    status_code: Optional[int] = Field(None, description="HTTP status code of the response")
    response: Optional[str] = Field(None, description="Response text from the webhook")
    sample_payload: str = Field(..., description="Sample payload sent to the webhook")
