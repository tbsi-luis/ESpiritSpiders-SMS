from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class SMSMessage(BaseModel):
    """
    Represents a single SMS message in a webhook payload.
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


class SMSWebhookPayload(BaseModel):
    """
    Model for SMS Mobile API webhook payload.
    Represents the data received when SMS(s) are delivered to the webhook endpoint.
    
    Supports both single message (backward compatibility) and batch messages.
    Provider retries are handled via guid deduplication.
    """
    # Single message format (backward compatible)
    date: Optional[str] = Field(None, description="Date when the SMS was added (YYYY-MM-DD)")
    hour: Optional[str] = Field(None, description="Hour when the SMS was added (HH:mm:ss)")
    time_received: Optional[str] = Field(None, description="Timestamp when SMS was received")
    message: Optional[str] = Field(None, description="Content of the SMS")
    number: Optional[str] = Field(None, description="Sender's phone number")
    guid: Optional[str] = Field(None, description="Unique identifier of the SMS")
    
    # Batch messages format (new)
    messages: Optional[List[SMSMessage]] = Field(None, description="List of SMS messages")
    
    def get_all_messages(self) -> List[SMSMessage]:
        """
        Extract all messages from payload, handling both single and batch formats.
        
        Returns:
            List of SMSMessage objects (empty list if no valid messages)
        """
        # If batch messages provided, use them
        if self.messages:
            return self.messages
        
        # Fallback to single message format (backward compatibility)
        if self.message and self.number and self.guid:
            return [SMSMessage(
                date=self.date or "",
                hour=self.hour or "",
                time_received=self.time_received or "",
                message=self.message,
                number=self.number,
                guid=self.guid
            )]
        
        return []
    
    class Config:
        json_schema_extra = {
            "example_single": {
                "date": "2025-01-20",
                "hour": "10:15:00",
                "time_received": "2025-01-20 10:14:50",
                "message": "Hello, this is a test.",
                "number": "+123456789",
                "guid": "abcde12345"
            },
            "example_batch": {
                "messages": [
                    {
                        "date": "2025-01-20",
                        "hour": "10:15:00",
                        "time_received": "2025-01-20 10:14:50",
                        "message": "Message 1",
                        "number": "+123456789",
                        "guid": "msg-001"
                    },
                    {
                        "date": "2025-01-20",
                        "hour": "10:16:00",
                        "time_received": "2025-01-20 10:15:50",
                        "message": "Message 2",
                        "number": "+123456789",
                        "guid": "msg-002"
                    }
                ]
            }
        }