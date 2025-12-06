import logging
import os
import re
from typing import Dict, List, Optional, Tuple
from langchain_openai import ChatOpenAI
from config import get_settings
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

settings = get_settings()

# =============================================================================
# STATIC CHECKER - Pattern-based agreement detection (English & Tagalog)
# =============================================================================
# This saves tokens by checking common patterns before calling OpenAI

# English agreement patterns
AGREE_PATTERNS_EN = [
    r'\byes\b', r'\byeah\b', r'\byup\b', r'\bsure\b', r'\bkay\b', 
    r'\bfine\b', r'\bwill do\b', r'\bconfirm\b', r'\bagree\b',
    r'\bdefnitely\b', r'\bsure thing\b', r'\bcount me in\b',
    r'\bI\'ll be there\b', r'\bon my way\b', r'\bI\'m in\b',
    r'\babsolutely\b', r'\bcertainly\b', r'\bof course\b',
    r'\ball good\b', r'\bno problem\b', r'\bgood to go\b',
    r'\bthanks\b', r'\bthanks for asking\b', r'\b✓\b', r'\b✅\b'
]

# English disagreement patterns
DISAGREE_PATTERNS_EN = [
    r'\bno\b', r'\bnope\b', r'\bcan\'t\b', r'\bcannot\b', r'\bcan not\b',
    r'\bwon\'t\b', r'\bwill not\b', r'\bunable\b', r'\bimpossible\b',
    r'\bsorry\b', r'\bsorry can\'t\b', r'\bnot available\b',
    r'\bnot possible\b', r'\bunable to\b', r'\bhave other plans\b',
    r'\balready committed\b', r'\bbusy\b', r'\blet you know\b',
    r'\bnot sure\b', r'\bmaybe later\b', r'\b✗\b', r'\b❌\b',
    r'\bcan\'t make it\b', r'\bcan\'t come\b'
]

# Tagalog agreement patterns
AGREE_PATTERNS_TL = [
    r'\boo\b', r'\byes\b', r'\byus\b', r'\baya\b', r'\bsige\b',
    r'\bokay\b', r'\bmalaki\b', r'\btama\b', r'\badmit\b',
    r'\bgo\b', r'\bkaya\b', r'\bkaya ko\b', r'\bgawin\b',
    r'\bpwede\b', r'\bmakakapunta\b', r'\bmeron\b', r'\bnaroroon ako\b',
    r'\broroon ako\b', r'\bpresente\b', r'\bkasama\b',
    r'\bmagsisikap\b', r'\bmakakasiguro\b'
]

# Tagalog disagreement patterns
DISAGREE_PATTERNS_TL = [
    r'\bhindi\b', r'\bhindot\b', r'\bno\b', r'\bnope\b',
    r'\bwala\b', r'\bwalang\b', r'\bnakakasama\b',
    r'\bhirip\b', r'\bbusy\b', r'\boccupado\b', r'\boccupada\b',
    r'\bmeron\bna\b', r'\bnakatuon\b', r'\bnakaengganyo\b',
    r'\bsorry\b', r'\bsorri\b', r'\bmagsisi\b',
    r'\bkayat\b', r'\bkayat ko\b', r'\bkaya hindi\b',
    r'\bumalis\b', r'\biwanan\b', r'\biwanan\b'
]


def static_check_agreement(text: str) -> Optional[bool]:
    """
    Perform static pattern-based check for agreement/disagreement.
    
    Args:
        text: Message text to check
    
    Returns:
        True if detected as "Agree", False if detected as "Disagree", 
        None if inconclusive (should use AI)
    
    This function checks common keywords in English and Tagalog to determine
    if a message indicates agreement or disagreement. If the message is
    ambiguous or contains mixed signals, returns None so the AI can decide.
    """
    if not text or not isinstance(text, str):
        return None
    
    # Normalize text: lowercase, strip whitespace
    normalized = text.lower().strip()
    
    # Remove common SMS prefixes/noise
    normalized = re.sub(r'^(re|fwd|reply)[\s:]*', '', normalized, flags=re.IGNORECASE)
    
    # Count matches for each category
    agree_score = 0
    disagree_score = 0
    
    # Check English patterns
    for pattern in AGREE_PATTERNS_EN:
        if re.search(pattern, normalized, re.IGNORECASE):
            agree_score += 1
    
    for pattern in DISAGREE_PATTERNS_EN:
        if re.search(pattern, normalized, re.IGNORECASE):
            disagree_score += 1
    
    # Check Tagalog patterns
    for pattern in AGREE_PATTERNS_TL:
        if re.search(pattern, normalized, re.IGNORECASE):
            agree_score += 1
    
    for pattern in DISAGREE_PATTERNS_TL:
        if re.search(pattern, normalized, re.IGNORECASE):
            disagree_score += 1
    
    # If no matches found, inconclusive - use AI
    if agree_score == 0 and disagree_score == 0:
        return None
    
    # If clear winner, return result (confident prediction)
    if agree_score > disagree_score:
        return True  # Agree
    elif disagree_score > agree_score:
        return False  # Disagree
    
    # If tied/mixed, inconclusive - use AI
    return None

def classify_message_with_openai(text: str) -> Tuple[bool, str]:
    """
    Classify a single reply into boolean (Agree=True, otherwise=False).
    
    Process:
    1. Try static pattern-based checker first (saves tokens)
    2. If inconclusive, call OpenAI API for intelligent classification
    
    Args:
        text: Message text to classify
    
    Returns:
        Tuple of (classification_result, method_used)
        - classification_result: True if Agree, False if not
        - method_used: "static" if pattern matched, "openai" if AI was used
    
    This hybrid approach significantly reduces token usage by handling
    common agreements/disagreements with fast pattern matching first.
    """
    
    # =====================================================================
    # STEP 1: Try static pattern-based checker first
    # =====================================================================
    static_result = static_check_agreement(text)
    
    if static_result is not None:
        # Pattern match was conclusive
        logger.info(f"Static check: {'AGREE' if static_result else 'DISAGREE'} | Text: {text[:50]}")
        return static_result, "static"
    
    # =====================================================================
    # STEP 2: Static check inconclusive, use OpenAI
    # =====================================================================
    api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
    model = settings.OPENAI_MODEL
    temp = float(getattr(settings, "OPENAI_TEMPERATURE", 0.0))

    if not api_key or ChatOpenAI is None:
        raise RuntimeError("OpenAI not configured")

    openai_client = ChatOpenAI(model_name="gpt-4o")

    system = (
        "You are a classifier that determines if a reply message shows agreement. "
        "The message may be in English, Tagalog, or mixed. "
        "Respond with exactly one of these words: Agree, Disagree, Neutral."
    )

    examples = (
        "Example 1:\nMessage: Let's meet at 6 PM.\nReply: Sure, that works for me.\nOutput: Agree\n\n"
        "Example 2:\nMessage: We should cancel the trip.\nReply: No way, we're still going.\nOutput: Disagree\n\n"
        "Example 3:\nMessage: Do you want to join the call?\nReply: Maybe, not sure yet.\nOutput: Neutral\n\n"
        "Example 4:\nMessage: Pwede ka ba bukas?\nReply: Oo sige, roroon ako.\nOutput: Agree\n\n"
        "Example 5:\nMessage: Pwede ka ba bukas?\nReply: Hindi, busy ako.\nOutput: Disagree\n\n"
    )

    user = f"Given the reply message:\n\n{repr(text)}\n\nReturn one word: Agree, Disagree, or Neutral."

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": examples + user},
    ]

    try:
        resp = openai_client.invoke(messages)
        
        # resp is an AIMessage object, extract content directly
        text_out = getattr(resp, "content", None)
        if text_out:
            cleaned = text_out.strip().split()[0].capitalize()
            result = cleaned == "Agree"  # True if Agree, else False
            logger.info(f"OpenAI check: {'AGREE' if result else 'DISAGREE'} | Text: {text[:50]}")
            return result, "openai"
        return False, "openai"

    except Exception as e:
        print(e)
        logger.warning(f"OpenAI classification failed: {e}")
        return False, "openai_failed"

def classify_messages(messages: List[Dict]) -> List[Dict]:
    """Classify a list of messages. Each dict should have a 'message' or 'text' field.

    Returns list of dicts with added boolean 'classification' key and 'method' key.
    """
    out = []
    for msg in messages:
        text = msg.get("message") or msg.get("text") or msg.get("body") or ""
        try:
            label, method = classify_message_with_openai(text)
        except Exception:
            raise RuntimeError("Classification failed")

        new = dict(msg)
        new["classification"] = label  # True or False
        new["method"] = method  # "static", "openai", or "openai_failed"
        out.append(new)

    return out

if __name__ == "__main__":
    # Example usage - test both English and Tagalog
    test_messages = [
        {"id": 1, "message": "Yes, I can attend the meeting."},
        {"id": 2, "message": "Yeah, sige!"},
        {"id": 3, "message": "No, I'll let you know later."},
        {"id": 4, "message": "Oo roroon ako bukas!"},
        {"id": 5, "message": "Hindi, busy ako."},
        {"id": 6, "message": "Maybe, not sure yet."},  # Should use AI (inconclusive)
    ]

    results = classify_messages(test_messages)
    for res in results:
        status = "✓ AGREE" if res['classification'] else "✗ DISAGREE"
        method = res.get('method', 'unknown')
        print(f"ID {res['id']}: {status} | Method: {method} | Message: {res['message'][:40]}")