import logging
import os
from typing import Dict, List

from config import get_settings

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None

logger = logging.getLogger(__name__)

settings = get_settings()


def _rule_based_classify(text: str) -> str:
    """Fallback lightweight classifier when OpenAI key is not set.

    Very simple heuristics: looks for affirmative/negative tokens.
    """
    if not text:
        return "Neutral"

    t = text.lower()
    # strong affirmative tokens
    affirm = ["yes", "yep", "yeah", "sure", "ok", "okay", "can", "will", "i can", "i'll", "i will", "agree", "affirmative", "works for me"]
    neg = ["no", "nah", "not", "can't", "cannot", "won't", "will not", "nope", "never", "refuse"]

    for token in affirm:
        if token in t:
            return "Agree"

    for token in neg:
        if token in t:
            return "Disagree"

    return "Neutral"


def classify_message_with_openai(text: str) -> str:
    """Call OpenAI to classify single reply into Agree/Disagree/Neutral.

    If OpenAI client is not available or no API key, raise RuntimeError so caller can fall back.
    """
    api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
    model = settings.OPENAI_MODEL
    temp = float(getattr(settings, "OPENAI_TEMPERATURE", 0.0))

    if not api_key or OpenAI is None:
        raise RuntimeError("OpenAI not configured")

    client = OpenAI(api_key=api_key)

    # Construct concise system + user prompt with examples
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
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temp,
            max_tokens=5
        )

        # Response format can vary; try to extract text
        choices = getattr(resp, "choices", None) or resp.get("choices")
        if choices and len(choices) > 0:
            text_out = choices[0].get("message", {}).get("content") if isinstance(choices[0], dict) else getattr(choices[0].message, "content", None)
            if text_out:
                cleaned = text_out.strip().split()[0].strip().capitalize()
                if cleaned in ("Agree", "Disagree", "Neutral"):
                    return cleaned

    except Exception as e:
        logger.warning(f"OpenAI classification failed: {e}")

    # If anything failed, fallback to rule-based
    return _rule_based_classify(text)


def classify_messages(messages: List[Dict]) -> List[Dict]:
    """Classify a list of message dicts. Each dict is expected to have a 'message' or 'text' field.

    Returns list of dicts with added 'classification' key.
    """
    out = []
    for msg in messages:
        text = msg.get("message") or msg.get("text") or msg.get("body") or ""
        label = "Neutral"
        # Prefer OpenAI if configured
        try:
            label = classify_message_with_openai(text)
        except RuntimeError:
            label = _rule_based_classify(text)
        except Exception:
            label = _rule_based_classify(text)

        new = dict(msg)
        new["classification"] = label
        out.append(new)

    return out
