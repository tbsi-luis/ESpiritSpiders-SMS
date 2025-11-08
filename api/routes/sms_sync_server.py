from fastapi import APIRouter, HTTPException, BackgroundTasks, Body
from services.reliever_service import get_relievers
from services.heads_service import get_head_admin
from helpers.date_filtering import _filter_today_reliever_messages
from services.classifier_service import classify_messages
from models.request_models import RelieverRequest, Reliever
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

# Model for response when sending to multiple relievers
class BulkSMSResponse(BaseModel):
    success: bool
    sent_to: List[Dict[str, str]]
    failed: List[Dict[str, str]]
    message: str

@router.post("/request-relievers", response_model=BulkSMSResponse)
async def send_to_relievers(
    request: RelieverRequest,
    background_tasks: BackgroundTasks = None
):
    """
    Send SMS to relievers provided in the request body.
    """
    check_sms_sender()

    if not request.relievers:
        raise HTTPException(
            status_code=400,
            detail="Relievers list cannot be empty."
        )

    sent_to = []
    failed = []

    def send_to_reliever(reliever: Reliever):
        try:
            logger.info(f"Sending SMS to {reliever.name} ({reliever.contact})")
            response = sms_sender.send_message(
                to=reliever.contact,
                message=request.message
            )
            sent_to.append({
                "name": reliever.name,
                "contact": reliever.contact,
                "response": response
            })
        except Exception as e:
            logger.error(f"Failed to send SMS to {reliever.name}: {e}")
            failed.append({
                "name": reliever.name,
                "contact": reliever.contact,
                "error": str(e)
            })

    # Use background sending if available
    if background_tasks:
        for reliever in request.relievers:
            background_tasks.add_task(send_to_reliever, reliever)
        return BulkSMSResponse(
            success=True,
            sent_to=[],
            failed=[],
            message="SMS sending queued for given relievers"
        )

    # Synchronous
    for reliever in request.relievers:
        send_to_reliever(reliever)

    return BulkSMSResponse(
        success=len(failed) == 0,
        sent_to=sent_to,
        failed=failed,
        message=f"SMS sent to {len(sent_to)} reliever(s). Failed: {len(failed)}"
    )

# retrieve + filter → forward to POST
@router.get("/relievers-reply", response_model=MessageResponse)
async def retrieve_replies(background_tasks: BackgroundTasks = None):
    """Fetch today’s reliever replies and hand them off for classification/notification."""
    check_sms_sender()

    try:
        logger.info("Fetching received messages (today only) for reliever classification")

        # 1. Raw data + reliever info
        raw_messages = sms_sender.get_received_messages()
        relievers = get_relievers()
        reliever_contacts = {r["contact"].replace("+", "") for r in relievers}
        contact_to_reliever = {r["contact"].replace("+", ""): r for r in relievers}

        # 2. Today boundaries (provider timezone)
        PROVIDER_TIMEZONE = "UTC"
        account_tz = pytz.timezone(PROVIDER_TIMEZONE)
        today_start = account_tz.localize(datetime.combine(date.today(), datetime.min.time()))

        # 3. Filter
        filtered = _filter_today_reliever_messages(
            raw_messages, reliever_contacts, account_tz, today_start
        )
        logger.info(f"Found {len(filtered)} reliever messages from today")

        if not filtered:
            return MessageResponse(
                success=True,
                message="No new reliever messages from today to process",
                data={"classified_count": 0, "classified_messages": [], "notified": []},
            )

        # 4. Forward to the dedicated classification endpoint
        return await classify_and_notify_relievers(
            background_tasks, filtered, contact_to_reliever
        )

    except Exception as exc:
        logger.error(f"Failed to retrieve reliever messages: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve reliever messages: {exc}")


# classification + notification ONLY (receives pre-filtered data)
@router.post("/relievers-reply/classify-and-notify", response_model=MessageResponse)
async def classify_and_notify_relievers(
    background_tasks: BackgroundTasks = None,
    messages: List[Dict] = None,
    contact_mapping: Dict[str, Dict] = None,
):
    """
    Classify **pre-filtered** reliever replies and notify the head admin for “Agree”.
    """
    if not messages:
        return MessageResponse(
            success=True,
            message="No messages provided for classification",
            data={"classified_count": 0, "classified_messages": [], "notified": []},
        )

    try:
        # 1. Classification
        classified = classify_messages(messages)   # returns list of dicts with .classification

        # 2. Notification (only for “Agree”)
        head = get_head_admin()
        head_contact = head.get("contact")
        if not head_contact:
            raise ValueError("Head admin contact not configured")

        notified = []

        def _send(head_to: str, reliever: dict, reply: str):
            txt = (
                "RELIEVER AGREEMENT NOTIFICATION\n\n"
                f"Name: {reliever.get('name', 'Unknown')}\n"
                f"Number: {reliever.get('contact', '')}\n"
                f"Reply: {reply}\n\n"
                "The reliever has agreed to the request."
            )
            try:
                sms_sender.send_message(to=head_to, message=txt)
                notified.append(
                    {"name": reliever.get("name"), "contact": reliever.get("contact"), "reply": reply}
                )
                logger.info(f"Notification sent to head for {reliever.get('name')}")
            except Exception as exc:
                logger.error(f"Failed to notify head ({head_to}): {exc}")

        for item in classified:
            if item.get("classification") != "Agree":
                continue

            sender = item.get("number") or item.get("from") or item.get("sender") or ""
            reliever = contact_mapping.get(sender.replace("+", ""), {"name": "Unknown", "contact": sender})
            reply_text = item.get("message") or item.get("text") or item.get("body") or ""

            if background_tasks:
                background_tasks.add_task(_send, head_contact, reliever, reply_text)
            else:
                _send(head_contact, reliever, reply_text)

        return MessageResponse(
            success=True,
            message="Classified today's reliever messages and sent notifications for agreed replies",
            data={
                "classified_count": len(classified),
                "classified_messages": classified,
                "notified": notified,
            },
        )

    except Exception as exc:
        logger.error(f"Failed to classify/notify reliever messages: {exc}")
        raise HTTPException(
            status_code=500, detail=f"Failed to classify/notify reliever messages: {exc}"
        )