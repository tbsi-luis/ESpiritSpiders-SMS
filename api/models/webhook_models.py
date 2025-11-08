from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class SMSWebhookPayload(BaseModel):
    """
    Model for SMS Mobile API webhook payload.
    Represents the data received when an SMS is delivered to the webhook endpoint.
    """
    date: str = Field(..., description="Date when the SMS was added (YYYY-MM-DD)")
    hour: str = Field(..., description="Hour when the SMS was added (HH:mm:ss)")
    time_received: str = Field(..., description="Timestamp when SMS was received")
    message: str = Field(..., description="Content of the SMS")
    number: str = Field(..., description="Sender's phone number")
    guid: str = Field(..., description="Unique identifier of the SMS")
    
    class Config:
        json_schema_extra = {
            "example": {
                "date": "2025-01-20",
                "hour": "10:15:00",
                "time_received": "2025-01-20 10:14:50",
                "message": "Hello, this is a test.",
                "number": "+123456789",
                "guid": "abcde12345"
            }
        }