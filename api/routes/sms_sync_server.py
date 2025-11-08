from fastapi import APIRouter, HTTPException, BackgroundTasks, Body
from models.head_notification_models import HeadNotificationRequest, HeadNotificationResult
from models.request_reliever_models import RelieverRequest, RelieverRequestNotificationResult
from models.webhook_models import SMSWebhookPayload
from services.analyze_reply_service import classify_messages, classify_message_with_openai
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from smsmobileapi import SMSSender
import os
from dotenv import load_dotenv
import logging
from openai import OpenAI
from config import get_settings
from datetime import datetime, date, timedelta
import pytz

load_dotenv()

settings = get_settings()

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["SMS Gateway"]
)

# Initialize SMS sender
API_KEY = os.getenv("SMS_MOBILE_API_KEY")
if not API_KEY:
    logger.warning("SMS_MOBILE_API_KEY not found in environment variables")
    
sms_sender = None
if API_KEY:
    try:
        sms_sender = SMSSender(api_key=API_KEY)
        logger.info("SMS Mobile API initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize SMS Mobile API: {e}")


# Pydantic models for request validation
class SMSRequest(BaseModel):
    to: str = Field(..., description="Phone number to send SMS to (with country code)")
    message: str = Field(..., description="Message content", max_length=1000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "to": "+639123456789",
                "message": "Hello from FastAPI!"
            }
        }

class MessageResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


# Helper function to check if SMS sender is initialized
def check_sms_sender():
    if not sms_sender:
        raise HTTPException(
            status_code=503,
            detail="SMS Mobile API not configured. Please set SMS_MOBILE_API_KEY in environment variables."
        )

# Endpoint to notify heads about absent employees
@router.post("/notify-heads", response_model=HeadNotificationResult)
async def notify_heads(
    request: HeadNotificationRequest,
    background_tasks: BackgroundTasks = None
):
    """
    Notify head admins about absent employees under their supervision.
    """
    check_sms_sender()

    sent_to = []
    failed = []

    # Collect all employees from the lists
    all_employees = []
    for emp_list in request.employees_under:
        all_employees.extend(emp_list.employees)

    if not all_employees:
        raise HTTPException(
            status_code=400,
            detail="Employee list cannot be empty."
        )

    if not request.head_list:
        raise HTTPException(
            status_code=400,
            detail="Head list cannot be empty."
        )

    # Send notifications to each head
    for head in request.head_list:
        try:
            # Construct message for absent employees
            notification_message = request.message + "\n\nThe following employees are absent today:\n"
            for emp in all_employees:
                notification_message += f"- {emp.name} ({emp.position})\n"

            logger.info(f"Notifying head {head.head_name} about {len(all_employees)} absent employees")
            response = sms_sender.send_message(
                to=head.contact_number,
                message=notification_message
            )
            sent_to.append({
                "name": head.head_name,
                "contact": head.contact_number,
                "response": response
            })
        except Exception as e:
            logger.error(f"Failed to notify head {head.head_name}: {e}")
            failed.append({
                "name": head.head_name,
                "error": str(e)
            })

    return HeadNotificationResult(
        success=len(failed) == 0,
        sent_to=sent_to,
        failed=failed,
        message=f"Notifications sent to {len(sent_to)} heads. Failed: {len(failed)}"
    )


# Endpoint to notify relievers
@router.post("/request-relievers", response_model=RelieverRequestNotificationResult)
async def notify_relievers(
    request: RelieverRequest,
    background_tasks: BackgroundTasks = None
):
    """
    Send personalized SMS messages to relievers.
    """
    check_sms_sender()

    sent_to = []
    failed = []

    if not request.relievers:
        raise HTTPException(
            status_code=400,
            detail="Reliever list cannot be empty."
        )

    for reliever in request.relievers:
        try:
            logger.info(f"Sending message to reliever {reliever.name} ({reliever.contact})")
            
            # Send SMS message
            response = sms_sender.send_message(
                to=reliever.contact,
                message=reliever.message
            )

            sent_to.append({
                "name": reliever.name,
                "contact": reliever.contact,
                "response": response
            })

        except Exception as e:
            logger.error(f"Failed to send message to {reliever.name}: {e}")
            failed.append({
                "name": reliever.name,
                "contact": reliever.contact,
                "error": str(e)
            })

    success = len(failed) == 0
    message_summary = f"Messages sent to {len(sent_to)} relievers. Failed: {len(failed)}"

    return RelieverRequestNotificationResult(
        success=success,
        sent_to=sent_to,
        failed=failed,
        message=message_summary
    )
    

# NEW: Webhook endpoint to receive incoming SMS
@router.post("/webhook/sms-received")
async def receive_sms_webhook(
    payload: SMSWebhookPayload,
    background_tasks: BackgroundTasks
):
    """
    Webhook endpoint to receive incoming SMS messages from SMS Mobile API.
    
    This endpoint receives POST requests when an SMS is received by the system.
    The payload includes message details like sender number, message content, and timestamp.
    """
    try:
        logger.info(f"Received SMS webhook from {payload.number}")
        logger.info(f"Message: {payload.message}")
        logger.info(f"Time received: {payload.time_received}")
        logger.info(f"GUID: {payload.guid}")
        
        # Process the SMS in the background to avoid blocking the webhook response
        background_tasks.add_task(process_incoming_sms, payload)
        
        # Return success response immediately
        return {
            "status": "success",
            "message": "Webhook received successfully",
            "guid": payload.guid
        }
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing webhook: {str(e)}"
        )


async def process_incoming_sms(payload: SMSWebhookPayload):
    """
    Process incoming SMS messages. This function runs in the background.
    
    Add your custom logic here to:
    - Classify the message (using your analyze_reply_service)
    - Store in database
    - Trigger automated responses
    - Send notifications
    """
    try:
        logger.info(f"Processing SMS from {payload.number}: {payload.message}")
        
        # Example: Classify the message using your existing service
        # Uncomment and modify based on your needs
        # classification = await classify_message_with_openai(payload.message)
        # logger.info(f"Message classified as: {classification}")
        
        # Example: Store in database (add your database logic here)
        # await store_sms_in_database(payload)
        
        # Example: Check if this is a reply to a reliever request
        # and handle accordingly
        # await handle_reliever_reply(payload)
        
        logger.info(f"Successfully processed SMS {payload.guid}")
        
    except Exception as e:
        logger.error(f"Error in background SMS processing: {e}")


# Optional: Endpoint to test webhook functionality
@router.post("/webhook/test")
async def test_webhook(request: SMSWebhookPayload):
    """
    Test endpoint to verify webhook setup.
    Logs the raw payload received.
    """
    try:
        logger.info(f"Test webhook received: {payload}")
        return {"status": "success", "received": payload}
    except Exception as e:
        logger.error(f"Test webhook error: {e}")
        return {"status": "error", "message": str(e)}