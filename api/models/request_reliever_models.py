from pydantic import BaseModel, Field
from typing import List, Optional
from typing import Optional, List, Dict

class Reliever(BaseModel):
    name: str
    contact: str
    message: str

class RelieverRequest(BaseModel):
    relievers: List[Reliever]

class NotificationResponse(BaseModel):
    name: str
    contact: str
    response: dict

class RelieverRequestNotificationResult(BaseModel):
    success: bool
    sent_to: List[NotificationResponse]
    failed: List[Dict[str, str]]
    message: str