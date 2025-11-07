from fastapi import APIRouter, HTTPException, BackgroundTasks, Body
from services.reliever_service import get_relievers
from services.heads_service import get_head_admin
from services.classifier_service import classify_messages
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from smsmobileapi import SMSSender
import os
from dotenv import load_dotenv
import logging
from openai import OpenAI
from config import get_settings

load_dotenv()

settings = get_settings()

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/mobile-sms",
    tags=["Mobile SMS"]
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


# Status endpoint
@router.get("/status")
async def get_status():
    """
    Check SMS Mobile API connection status
    """
    return {
        "service": "SMS Mobile API",
        "configured": sms_sender is not None,
        "ready": sms_sender is not None
    }


# Send SMS endpoint
@router.post("/send", response_model=MessageResponse)
async def send_sms(request: SMSRequest):
    """
    Send an SMS message via your mobile phone
    
    - **to**: Phone number with country code (e.g., +639123456789)
    - **message**: Text message to send
    """
    check_sms_sender()
    
    try:
        logger.info(f"Sending SMS to {request.to}")
        response = sms_sender.send_message(
            to=request.to,
            message=request.message
        )
        
        logger.info(f"SMS sent successfully to {request.to}")
        return MessageResponse(
            success=True,
            message="SMS sent successfully",
            data=response
        )
    
    except Exception as e:
        logger.error(f"Failed to send SMS to {request.to}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send SMS: {str(e)}"
        )


# Get received SMS messages
@router.get("/received", response_model=MessageResponse)
async def get_received_messages():
    """
    Retrieve all SMS messages received on your mobile phone
    """
    check_sms_sender()
    
    try:
        logger.info("Retrieving received messages")
        received = sms_sender.get_received_messages()
        
        logger.info(f"Retrieved {len(received) if isinstance(received, list) else 0} messages")
        return MessageResponse(
            success=True,
            message="Received messages retrieved successfully",
            data={"messages": received}
        )
    
    except Exception as e:
        logger.error(f"Failed to retrieve messages: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve messages: {str(e)}"
        )

# Get received SMS messages from relievers only
@router.get("/received/relievers", response_model=MessageResponse)
async def get_received_messages_from_relievers():
    """
    Retrieve SMS messages received only from configured relievers
    """
    check_sms_sender()
    
    try:
        logger.info("Retrieving received messages from relievers")
        
        # Get all received messages
        all_messages = sms_sender.get_received_messages()
        
        # Get reliever contact numbers (normalize by removing + prefix)
        relievers = get_relievers()
        reliever_contacts = {reliever["contact"].replace("+", "") for reliever in relievers}
        
        # Filter messages from relievers only
        filtered_messages = []
        
        # Handle nested structure: messages.result.sms
        messages_list = []
        if isinstance(all_messages, dict):
            result = all_messages.get("result", {})
            messages_list = result.get("sms", [])
        elif isinstance(all_messages, list):
            messages_list = all_messages
            
        for msg in messages_list:
            # Get sender number and normalize (remove + if present)
            sender = msg.get("number") or msg.get("from") or msg.get("sender")
            if sender:
                normalized_sender = sender.replace("+", "")
                if normalized_sender in reliever_contacts:
                    filtered_messages.append(msg)
        
        logger.info(f"Retrieved {len(filtered_messages)} messages from relievers")
        return MessageResponse(
            success=True,
            message="Received messages from relievers retrieved successfully",
            data={
                "messages": filtered_messages,
                "count": len(filtered_messages),
                "reliever_names": [reliever["name"] for reliever in relievers],
                "reliever_contacts": list(reliever_contacts)
            }
        )
    
    except Exception as e:
        logger.error(f"Failed to retrieve messages from relievers: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve messages: {str(e)}"
        )


@router.post("/received/relievers/classify-and-notify", response_model=MessageResponse)
async def classify_and_notify_relievers(background_tasks: BackgroundTasks = None):
    """
    Retrieve messages from relievers, classify replies (Agree/Disagree/Neutral),
    and notify head for relievers that replied with 'Agree'.
    """
    check_sms_sender()

    try:
        logger.info("Retrieving received messages from relievers for classification")

        # Get all received messages
        all_messages = sms_sender.get_received_messages()

        # Get reliever contact numbers and mapping
        relievers = get_relievers()
        reliever_contacts = {reliever["contact"].replace("+", "") for reliever in relievers}
        contact_to_reliever = {reliever["contact"].replace("+", ""): reliever for reliever in relievers}

        # Extract messages list (handle nested structures)
        messages_list = []
        if isinstance(all_messages, dict):
            result = all_messages.get("result", {})
            messages_list = result.get("sms", [])
        elif isinstance(all_messages, list):
            messages_list = all_messages

        filtered_messages = []
        for msg in messages_list:
            sender = msg.get("number") or msg.get("from") or msg.get("sender")
            if sender:
                normalized_sender = sender.replace("+", "")
                if normalized_sender in reliever_contacts:
                    filtered_messages.append(msg)

        logger.info(f"Classifying {len(filtered_messages)} reliever messages")

        # Classify messages (service will fallback to rule-based if OpenAI not configured)
        classified = classify_messages(filtered_messages)

        # Notify head for agreed relievers
        head = get_head_admin()
        head_contact = head.get("contact")

        notified = []

        def send_notification(head_to: str, reliever: dict, reply_text: str):
            notification_text = (
                "RELIEVER AGREEMENT NOTIFICATION\n\n"
                f"Name: {reliever.get('name', 'Unknown')}\n"
                f"Number: {reliever.get('contact', '')}\n"
                f"Reply: {reply_text}\n\n"
                "The reliever has agreed to the request."
            )
            try:
                sms_sender.send_message(to=head_to, message=notification_text)
                notified.append({
                    "name": reliever.get("name"),
                    "contact": reliever.get("contact"),
                    "reply": reply_text
                })

            except Exception as e:
                logger.error(f"Failed to send notification to head: {e}")

        # Iterate and notify either synchronously or via background tasks
        for item in classified:
            label = item.get("classification")
            if label == "Agree":
                sender = item.get("number") or item.get("from") or item.get("sender") or ""
                normalized = sender.replace("+", "")
                reliever = contact_to_reliever.get(normalized, {"name": "Unknown", "contact": sender})
                reply_text = item.get("message") or item.get("text") or item.get("body") or ""

                if background_tasks:
                    background_tasks.add_task(send_notification, head_contact, reliever, reply_text)
                else:
                    send_notification(head_contact, reliever, reply_text)

        return MessageResponse(
            success=True,
            message="Classified reliever messages and sent notifications for agreed replies",
            data={
                "classified_count": len(classified),
                "classified_messages": classified,
                "notified": notified,
            }
        )

    except Exception as e:
        logger.error(f"Failed to classify/notify reliever messages: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to classify/notify reliever messages: {str(e)}"
        )


@router.get("/relievers")
async def list_relievers():
    """
    List all configured static relievers
    """
    return {
        "relievers": get_relievers()
    }

# Model for response when sending to multiple relievers
class BulkSMSResponse(BaseModel):
    success: bool
    sent_to: List[Dict[str, str]]
    failed: List[Dict[str, str]]
    message: str

@router.post("/send-to-relievers", response_model=BulkSMSResponse)
async def send_to_relievers(
    message: str = Body(..., description="Message to send to all 3 relievers"),
    background_tasks: BackgroundTasks = None
):
    """
    Send availability request SMS to 3 static relievers
    """
    check_sms_sender()
    
    relievers = get_relievers()
    if len(relievers) < 2:
        raise HTTPException(
            status_code=500,
            detail="Not enough relievers configured. Need at least 3."
        )

    selected = relievers[:2]
    sent_to = []
    failed = []

    def send_to_reliever(reliever):
        try:
            logger.info(f"Sending SMS to {reliever['name']} ({reliever['contact']})")
            response = sms_sender.send_message(
                to=reliever["contact"],
                message=message
            )
            sent_to.append({
                "name": reliever["name"],
                "contact": reliever["contact"],
                "response": response
            })
            logger.info(f"SMS sent to {reliever['name']}")
        except Exception as e:
            logger.error(f"Failed to send SMS to {reliever['name']}: {e}")
            failed.append({
                "name": reliever["name"],
                "contact": reliever["contact"],
                "error": str(e)
            })

    # Use background tasks if provided, otherwise run sync
    if background_tasks:
        for reliever in selected:
            background_tasks.add_task(send_to_reliever, reliever)
        return BulkSMSResponse(
            success=True,
            sent_to=[],
            failed=[],
            message="SMS sending queued for 3 relievers"
        )
    else:
        # Synchronous mode (for testing or direct calls)
        for reliever in selected:
            send_to_reliever(reliever)

        return BulkSMSResponse(
            success=len(failed) == 0,
            sent_to=sent_to,
            failed=failed,
            message=f"SMS sent to {len(sent_to)} reliever(s). Failed: {len(failed)}"
        )

