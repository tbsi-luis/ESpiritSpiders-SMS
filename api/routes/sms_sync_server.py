"""
SMS Gateway API Routes
======================
This module handles SMS-related operations including:
1. Sending notifications to heads about absent employees
2. Sending personalized messages to relievers
3. Receiving and processing incoming SMS webhooks
4. Classifying incoming messages using AI or rule-based fallback
5. Sending optional auto-replies to incoming messages

All webhook processing runs asynchronously in the background to ensure
fast webhook acknowledgment (required by SMS providers).
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from models.head_notification_models import HeadNotificationRequest, HeadNotificationResult
from models.request_reliever_models import RelieverRequest, RelieverRequestNotificationResult
from models.webhook_models import SMSWebhookPayload, SMSMessage
from services.analyze_reply_service import classify_messages, classify_message_with_openai
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from smsmobileapi import SMSSender
import os
from dotenv import load_dotenv
import logging
from config import get_settings
from datetime import datetime
import pytz
import asyncio
from threading import Lock
from collections import deque

# =============================================================================
# INITIALIZATION & CONFIGURATION
# =============================================================================

load_dotenv()  # Load environment variables from .env file
settings = get_settings()  # Load app configuration
logger = logging.getLogger(__name__)  # Logger for this module

# Create FastAPI router with prefix and tags for API documentation
router = APIRouter(
    prefix="/api",
    tags=["SMS Gateway"]
)

# Initialize SMS Mobile API client
# - Reads SMS_MOBILE_API_KEY from environment
# - Creates SMSSender instance if key is available
# - Logs warnings/errors if initialization fails
API_KEY = os.getenv("SMS_MOBILE_API_KEY")
if not API_KEY:
    logger.warning("SMS_MOBILE_API_KEY not found in environment variables")

sms_sender = None
sms_sender_lock = Lock()  # Thread-safe access to sms_sender

if API_KEY:
    try:
        sms_sender = SMSSender(api_key=API_KEY)
        logger.info("SMS Mobile API initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize SMS Mobile API: {e}")

# =============================================================================
# DEDUPLICATION CACHE
# =============================================================================
# Prevent reprocessing of duplicate messages from provider retries
# Stores up to 1000 recently processed GUIDs with LRU eviction
_processed_message_guids: deque = deque(maxlen=1000)
_guid_lock = Lock()


def _mark_message_processed(guid: str) -> bool:
    """
    Mark a message GUID as processed.
    
    Returns:
        True if this is a new message, False if already processed (duplicate)
    """
    with _guid_lock:
        if guid in _processed_message_guids:
            return False  # Already processed
        _processed_message_guids.append(guid)
        return True  # First time processing


def _reset_deduplication_cache():
    """Clear the deduplication cache (useful for testing)."""
    with _guid_lock:
        _processed_message_guids.clear()


# =============================================================================
# PYDANTIC MODELS (Request/Response validation)
# =============================================================================

class SMSRequest(BaseModel):
    """
    Request model for sending a single SMS message.
    
    Fields:
    - to: Recipient phone number with country code (e.g., "+639123456789")
    - message: SMS text content (max 1000 characters)
    """
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
    """
    Generic response model for SMS operations.
    
    Fields:
    - success: Boolean indicating if operation succeeded
    - message: Human-readable status message
    - data: Optional dictionary with additional response data
    """
    success: bool
    message: str
    data: Optional[dict] = None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def check_sms_sender():
    """
    Validate that SMS Mobile API is properly configured.
    
    Raises:
        HTTPException (503): If SMS_MOBILE_API_KEY is not set in environment
    
    Usage:
        Called at the start of endpoints that send SMS to ensure the sender
        is initialized before attempting to send messages.
    """
    if not sms_sender:
        raise HTTPException(
            status_code=503,
            detail="SMS Mobile API not configured. Please set SMS_MOBILE_API_KEY in environment variables."
        )


# =============================================================================
# ENDPOINT 1: Notify Heads About Absent Employees
# =============================================================================

@router.post("/notify-heads", response_model=HeadNotificationResult)
async def notify_heads(
    request: HeadNotificationRequest,
    background_tasks: BackgroundTasks = None
):
    """
    Send SMS notifications to head admins about their absent employees.
    
    Process:
    1. Validate SMS sender is initialized
    2. Collect all employees from the request's employee lists
    3. Validate employee and head lists are not empty
    4. For each head:
       - Construct a message listing all absent employees
       - Send SMS via SMS Mobile API
       - Track success/failure
    5. Return results with sent count and failures
    
    Args:
        request: HeadNotificationRequest containing heads and employees lists
        background_tasks: FastAPI background tasks (not used currently)
    
    Returns:
        HeadNotificationResult with success status, sent list, and failed list
    
    Raises:
        HTTPException (400): If employee or head list is empty
        HTTPException (503): If SMS sender not configured
    """
    check_sms_sender()

    sent_to = []  # Track successful notifications
    failed = []   # Track failed notifications

    # Collect all employees from all employee lists in the request
    all_employees = []
    for emp_list in request.employees_under:
        all_employees.extend(emp_list.employees)

    # Validation: employees cannot be empty
    if not all_employees:
        raise HTTPException(
            status_code=400,
            detail="Employee list cannot be empty."
        )

    # Validation: head list cannot be empty
    if not request.head_list:
        raise HTTPException(
            status_code=400,
            detail="Head list cannot be empty."
        )

    # Send notification to each head
    for head in request.head_list:
        try:
            # Construct the notification message
            notification_message = request.message + "\n\nThe following employees are absent today:\n"
            for emp in all_employees:
                notification_message += f"- {emp.name} ({emp.position})\n"

            logger.info(f"Notifying head {head.head_name} about {len(all_employees)} absent employees")
            
            # Send SMS via provider
            response = sms_sender.send_message(
                to=head.contact_number,
                message=notification_message
            )
            
            # Record successful send
            sent_to.append({
                "name": head.head_name,
                "contact": head.contact_number,
                "response": response
            })
        except Exception as e:
            logger.error(f"Failed to notify head {head.head_name}: {e}")
            # Record failure for this head
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


# =============================================================================
# ENDPOINT 2: Notify Relievers
# =============================================================================

@router.post("/request-relievers", response_model=RelieverRequestNotificationResult)
async def notify_relievers(
    request: RelieverRequest,
    background_tasks: BackgroundTasks = None
):
    """
    Send personalized SMS messages to relievers.
    
    Process:
    1. Validate SMS sender is initialized
    2. Validate reliever list is not empty
    3. For each reliever:
       - Send personalized SMS message
       - Track success/failure
    4. Return results with sent count and failures
    
    Args:
        request: RelieverRequest containing list of relievers and their messages
        background_tasks: FastAPI background tasks (not used currently)
    
    Returns:
        RelieverRequestNotificationResult with success status, sent list, and failed list
    
    Raises:
        HTTPException (400): If reliever list is empty
        HTTPException (503): If SMS sender not configured
    """
    check_sms_sender()

    sent_to = []  # Track successful sends
    failed = []   # Track failed sends

    if not request.relievers:
        raise HTTPException(
            status_code=400,
            detail="Reliever list cannot be empty."
        )

    # Send message to each reliever
    for reliever in request.relievers:
        try:
            logger.info(f"Sending message to reliever {reliever.name} ({reliever.contact})")
            
            # Send SMS via provider
            response = sms_sender.send_message(
                to=reliever.contact,
                message=reliever.message
            )

            # Record successful send
            sent_to.append({
                "name": reliever.name,
                "contact": reliever.contact,
                "response": response
            })

        except Exception as e:
            logger.error(f"Failed to send message to {reliever.name}: {e}")
            # Record failure for this reliever
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


# =============================================================================
# ENDPOINT 3: Webhook Health Check (GET)
# =============================================================================

@router.get("/webhook/sms-received")
async def webhook_health_check():
    """
    Health check endpoint for webhook connectivity verification.
    
    Purpose:
    SMS Mobile API performs a GET request to this endpoint before sending actual
    webhook POSTs. This confirms the endpoint is reachable and the service is running.
    
    Response:
    Returns a 200 status with health check metadata.
    
    Note:
    This should respond quickly; it's a connectivity test, not actual SMS processing.
    """
    logger.info("Webhook health check received")
    return {
        "status": "ok",
        "message": "Webhook endpoint is active and ready to receive SMS",
        "timestamp": datetime.now(pytz.UTC).isoformat()
    }


# =============================================================================
# ENDPOINT 4: Webhook SMS Receiver (POST)
# =============================================================================

@router.post("/webhook/sms-received")
async def receive_sms_webhook(
    payload: SMSWebhookPayload,
    background_tasks: BackgroundTasks
):
    """
    Receive incoming SMS webhooks from SMS Mobile API.
    
    Process Flow:
    1. Extract all messages from payload (supports both single and batch formats)
    2. For each message:
       - Check if already processed (deduplication)
       - Enqueue background processing task (non-blocking)
    3. Return 200 success immediately (required by webhook standards)
    4. Background tasks classify messages and send optional auto-replies
    
    Batch Processing:
    - Handles multiple SMS in a single webhook call
    - Each message processed independently
    - Partial failures don't affect other messages
    
    Deduplication:
    - Uses message GUID to detect retries from provider
    - Prevents duplicate classifications and auto-replies
    - Maintains in-memory cache of recent GUIDs
    
    Args:
        payload: SMSWebhookPayload containing SMS message(s)
        background_tasks: FastAPI background tasks manager
    
    Returns:
        Dictionary with status, processed count, and skipped count
    
    Important:
        ALWAYS respond with 200 before doing heavy work. SMS providers expect
        fast responses and will retry if they don't get 2xx within timeout.
    """
    try:
        # Extract all messages (handles single + batch formats)
        messages = payload.get_all_messages()
        
        if not messages:
            logger.warning("Webhook received but no valid messages found")
            return {
                "status": "success",
                "message": "Webhook received but no messages to process",
                "processed": 0,
                "skipped": 0
            }
        
        # OPTIMIZATION: Queue all messages for background processing immediately
        # Deduplication check moved to background task to keep webhook response fast
        # (should respond in <10ms, not blocked by logging or dedup checks)
        
        for msg in messages:
            # Enqueue background processing (non-blocking)
            # Dedup check happens in the background task
            background_tasks.add_task(process_incoming_sms, msg)
        
        # Return success response immediately (within 5ms)
        # SMS provider expects fast response; slow webhook causes retries
        return {
            "status": "success",
            "message": f"Received {len(messages)} message(s), processing in background",
            "message_count": len(messages)
        }
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing webhook: {str(e)}"
        )


# =============================================================================
# BACKGROUND TASK: Process Incoming SMS
# =============================================================================

# =============================================================================
# BACKGROUND TASK: Process Incoming SMS
# =============================================================================

# async def process_incoming_sms(msg: SMSMessage):
#     """
#     Process a single incoming SMS in the background (runs after webhook response).
    
#     This function handles all the heavy lifting AFTER the webhook returns to the provider.
#     Webhook returns immediately to ensure fast acknowledgment; heavy work happens here.
    
#     Process Flow:
#     1. Check for duplicate message (dedup check moved from webhook for speed)
#     2. Log message receipt (moved from webhook to avoid blocking)
#     3. Classify message using OpenAI or rule-based fallback
#     4. Optionally send auto-reply
#     5. Handle all errors gracefully
    
#     Args:
#         msg: SMSMessage object containing all message details
    
#     Classification:
#     - Uses classify_message_with_openai() for AI-powered classification
#     - Falls back to classify_messages() with rule-based heuristics if OpenAI fails
#     - Result is boolean: True = "Agree", False = "Not Agree/Neutral"
    
#     Auto-Reply:
#     - Enabled by: SMS_AUTO_REPLY_ENABLED environment variable ("1", "true", "yes")
#     - Message text: SMS_AUTO_REPLY_TEXT env var or smart default based on classification
#     - Only sends if sms_sender is configured
    
#     Error Handling:
#     - All exceptions are caught and logged
#     - Processing failures don't crash the service
#     - Each step is resilient with fallbacks
#     """
#     try:
#         # =====================================================================
#         # STEP 0: Check for duplicates (from webhook retries)
#         # =====================================================================
#         # This check was moved here from the webhook to keep the webhook response fast
#         if not _mark_message_processed(msg.guid):
#             logger.info(f"Skipping duplicate message: {msg.guid}")
#             return  # Exit early, don't process duplicate
        
#         # =====================================================================
#         # STEP 1: Log message receipt
#         # =====================================================================
#         # Moved from webhook response to avoid blocking the webhook
#         logger.info(f"Processing SMS {msg.guid} from {msg.number}")
#         logger.debug(f"Message content: {msg.message}")

#         text = msg.message or ""

#         # =====================================================================
#         # STEP 2: Classify the message
#         # =====================================================================
        
#         classification = None
        
#         # Try primary classification method: OpenAI API
#         try:
#             classification = await asyncio.to_thread(classify_message_with_openai, text)
#             logger.info(f"Message {msg.guid} classified using OpenAI API")
        
#         # Fallback 1: OpenAI not configured (no API key)
#         except RuntimeError:
#             logger.info(f"Message {msg.guid}: OpenAI not configured, using rule-based fallback")
#             res = await asyncio.to_thread(classify_messages, [{"message": text}])
#             classification = bool(res[0].get("classification", False))
        
#         # Fallback 2: OpenAI API call failed (network, rate limit, etc.)
#         except Exception as e:
#             logger.warning(f"Message {msg.guid}: Classification via OpenAI failed, using fallback: {e}")
#             res = await asyncio.to_thread(classify_messages, [{"message": text}])
#             classification = bool(res[0].get("classification", False))

#         # Log the classification result
#         result_text = "Agree" if classification else "Not Agree/Neutral"
#         logger.info(f"Message {msg.guid} classified as: {result_text}")

#         # =====================================================================
#         # STEP 3: Optionally send auto-reply
#         # =====================================================================
        
#         # Check if auto-reply is enabled via environment variable
#         auto_reply_enabled = os.getenv("SMS_AUTO_REPLY_ENABLED", "false").lower() in ("1", "true", "yes")
        
#         if auto_reply_enabled:
#             # Verify SMS sender is configured
#             if not sms_sender:
#                 logger.warning(f"Message {msg.guid}: Auto-reply enabled but SMS sender not configured")
#             else:
#                 # Determine reply message
#                 # - Use custom text from env var if provided
#                 # - Otherwise use smart default based on classification
#                 reply_text = os.getenv("SMS_AUTO_REPLY_TEXT") or \
#                              ("Thanks for confirming." if classification else "Thanks for your reply.")
                
#                 try:
#                     logger.info(f"Sending auto-reply to {msg.number} for message {msg.guid}")
#                     with sms_sender_lock:
#                         sms_sender.send_message(to=msg.number, message=reply_text)
#                     logger.info(f"Auto-reply sent successfully to {msg.number}")
#                 except Exception as e:
#                     logger.error(f"Failed to send auto-reply to {msg.number}: {e}")

#         # =====================================================================
#         # STEP 4: Log successful processing
#         # =====================================================================
#         logger.info(f"Successfully completed processing for SMS {msg.guid}")

#     # Catch any unexpected errors to prevent background task crash
#     except Exception as e:
#         logger.error(f"Unexpected error in background SMS processing for message: {e}", exc_info=True)

async def process_incoming_sms(msg: SMSMessage):
    try:
        # Deduplication
        if not _mark_message_processed(msg.guid):
            logger.info(f"DUPLICATE IGNORED | GUID: {msg.guid} | From: {msg.number}")
            return

        # Clean phone number display (optional: format nicely)
        clean_number = msg.number.replace("+63", "0") if msg.number.startswith("+63") else msg.number

        # === RECEIVED MESSAGE ===
        logger.info(
            f"SMS RECEIVED | From: {clean_number} | GUID: {msg.guid} | "
            f"Text: \"{msg.message.strip()}\""
        )

        text = msg.message or ""

        classification = None

        # === CLASSIFICATION ===
        try:
            classification = await asyncio.to_thread(classify_message_with_openai, text)
            method = "OpenAI"
        except RuntimeError:
            logger.info(f"OPENAI UNAVAILABLE → Using rule-based fallback | From: {clean_number}")
            res = await asyncio.to_thread(classify_messages, [{"message": text}])
            classification = bool(res[0].get("classification", False))
            method = "Rule-based"
        except Exception as e:
            logger.warning(f"OPENAI FAILED → Fallback used | Error: {e} | From: {clean_number}")
            res = await asyncio.to_thread(classify_messages, [{"message": text}])
            classification = bool(res[0].get("classification", False))
            method = "Rule-based (after failure)"

        result_text = "AGREE" if classification else "NOT AGREE"
        emoji = "Yes" if classification else "No"

        # === CLASSIFICATION RESULT ===
        logger.info(
            f"CLASSIFIED AS {result_text} {emoji} | "
            f"From: {clean_number} | "
            f"Method: {method} | "
            f"GUID: {msg.guid}"
        )

        # === AUTO-REPLY (if enabled) ===
        auto_reply_enabled = os.getenv("SMS_AUTO_REPLY_ENABLED", "false").lower() in ("1", "true", "yes")
        
        if auto_reply_enabled and sms_sender:
            reply_text = os.getenv("SMS_AUTO_REPLY_TEXT") or \
                         ("Thanks for confirming! See you soon." if classification else "Thank you for replying.")

            try:
                with sms_sender_lock:
                    sms_sender.send_message(to=msg.number, message=reply_text)
                logger.info(f"AUTO-REPLY SENT | To: {clean_number} | \"{reply_text}\"")
            except Exception as e:
                logger.error(f"AUTO-REPLY FAILED | To: {clean_number} | Error: {e}")
        elif auto_reply_enabled and not sms_sender:
            logger.warning("AUTO-REPLY ENABLED but SMS sender not configured!")

        # === FINAL SUCCESS ===
        logger.info(f"PROCESSING COMPLETE | From: {clean_number} | Result: {result_text}")

    except Exception as e:
        logger.error(f"PROCESSING FAILED | GUID: {msg.guid} | From: {msg.number} | Error: {e}", exc_info=True)