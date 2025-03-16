from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class EmailMonitorBase(BaseModel):
    email_address: EmailStr = Field(...,
                                    description="Email address to monitor")
    filter_subject: Optional[str] = Field(
        None, description="Filter emails by subject (case-insensitive)")
    filter_sender: Optional[EmailStr] = Field(
        None, description="Filter emails by sender")
    check_interval_seconds: int = Field(
        60, ge=30, description="How often to check for new emails (in seconds)")
    active: bool = Field(
        True, description="Whether this monitor configuration is active")


class EmailMonitorCreate(EmailMonitorBase):
    pass


class EmailMonitorUpdate(BaseModel):
    email_address: Optional[EmailStr] = Field(
        None, description="Email address to monitor")
    filter_subject: Optional[str] = Field(
        None, description="Filter emails by subject (case-insensitive)")
    filter_sender: Optional[EmailStr] = Field(
        None, description="Filter emails by sender")
    check_interval_seconds: Optional[int] = Field(
        None, ge=30, description="How often to check for new emails (in seconds)")
    active: Optional[bool] = Field(
        None, description="Whether this monitor configuration is active")


class EmailMonitorInDB(EmailMonitorBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
