import logging
import os
from typing import Dict, List
from langchain_openai import ChatOpenAI
from config import get_settings
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

settings = get_settings()

def classify_message_with_openai(text: str) -> bool:
    """Call OpenAI to classify single reply into boolean (Agree=True, otherwise=False)."""
    api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
    model = settings.OPENAI_MODEL
    temp = float(getattr(settings, "OPENAI_TEMPERATURE", 0.0))

    if not api_key or ChatOpenAI is None:
        raise RuntimeError("OpenAI not configured")

    openai_client = ChatOpenAI(model_name = "gpt-4o")

    system = (
        "You are a classifier that determines if a reply message shows agreement. "
        "Respond with exactly one of these words: Agree, Disagree, Neutral."
    )

    examples = (
        "Example 1:\nMessage: Let's meet at 6 PM.\nReply: Sure, that works for me.\nOutput: Agree\n\n"
        "Example 2:\nMessage: We should cancel the trip.\nReply: No way, we're still going.\nOutput: Disagree\n\n"
        "Example 3:\nMessage: Do you want to join the call?\nReply: Maybe, not sure yet.\nOutput: Neutral\n\n"
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
            return cleaned == "Agree"  # True if Agree, else False
        return False

    except Exception as e:
        print(e)
        logger.warning(f"OpenAI classification failed: {e}")
        return False

def classify_messages(messages: List[Dict]) -> List[Dict]:
    """Classify a list of messages. Each dict should have a 'message' or 'text' field.

    Returns list of dicts with added boolean 'classification' key.
    """
    out = []
    for msg in messages:
        text = msg.get("message") or msg.get("text") or msg.get("body") or ""
        try:
            label = classify_message_with_openai(text)
        except Exception:
            raise RuntimeError("OpenAI classification failed")

        new = dict(msg)
        new["classification"] = label  # True or False
        out.append(new)

    return out

if __name__ == "__main__":
    # Example usage
    test_messages = [
        {"id": 1, "message": "Yes, I can attend the meeting."},
        {"id": 2, "message": "Yes, I wwll."},
        {"id": 3, "message": "No, I'll let you know later."},
    ]

    results = classify_messages(test_messages)
    for res in results:
        print(f"Message ID: {res['id']}, Classification: {res['classification']}")