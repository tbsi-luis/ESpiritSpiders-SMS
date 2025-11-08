from typing import Optional, List, Dict
from datetime import datetime, date, timedelta
import pytz

def _filter_today_reliever_messages(
    raw_messages: List | Dict,
    reliever_contacts: set[str],
    account_tz: pytz.BaseTzInfo,
    today_start: datetime,
) -> List[Dict]:
    """Return a list of messages that are (a) from a known reliever and (b) received today."""
    # Normalise the incoming payload into a flat list
    if isinstance(raw_messages, dict):
        messages = raw_messages.get("result", {}).get("sms", [])
    elif isinstance(raw_messages, list):
        messages = raw_messages
    else:
        messages = []

    filtered = []
    for msg in messages:
        # ---- sender -------------------------------------------------------
        sender = msg.get("number") or msg.get("from") or msg.get("sender")
        if not sender:
            continue
        if sender.replace("+", "") not in reliever_contacts:
            continue

        # ---- timestamp ----------------------------------------------------
        ts_raw = (
            msg.get("date")
            or msg.get("timestamp")
            or msg.get("received_at")
            or msg.get("sent_at")
            or msg.get("time")
        )
        if not ts_raw:
            logger.debug(f"Message from {sender} missing timestamp – skipping")
            continue

        try:
            if isinstance(ts_raw, (int, float)):
                ts = ts_raw / 1000 if ts_raw > 10**12 else ts_raw
                dt = datetime.fromtimestamp(ts, tz=pytz.UTC)
            else:
                ts_str = ts_raw.replace("Z", "+00:00")
                dt = datetime.fromisoformat(ts_str)
                if dt.tzinfo is None:
                    dt = pytz.UTC.localize(dt)
        except Exception as exc:
            logger.debug(f"Failed to parse timestamp '{ts_raw}' from {sender}: {exc}")
            continue

        # ---- today filter -------------------------------------------------
        if dt.astimezone(account_tz) < today_start:
            continue

        filtered.append(msg)

    return filtered