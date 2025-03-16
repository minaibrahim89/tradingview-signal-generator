from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
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
