# Message Consolidation Implementation (60-Second Window)

## Overview
Messages from the **same sender** arriving within a **60-second window** are now automatically consolidated before classification. This prevents duplicate API calls and classifies multiple related messages as a unified response.

---

## How It Works

### Flow Diagram
```
Webhook receives message from +639123456789
    ↓
Check if GUID already processed (dedup)
    ↓
First message from this number? 
    ├─ YES: Create buffer, start 60-second timer
    └─ NO: Add to existing buffer
    ↓
Wait 60 seconds for more messages from same sender
    ↓
Timer expires → Consolidate all buffered messages
    ↓
Send combined text to classifier (ONE API call for multiple messages)
    ↓
Send ONE auto-reply for entire batch
```

### Key Components

#### 1. **Consolidation Cache** (lines 76-133)
```python
_sender_message_buffer: Dict[str, Dict] = {}
_buffer_lock = Lock()
CONSOLIDATION_WINDOW = 60  # seconds
```

Per-sender buffer structure:
- **Key**: Phone number (e.g., "+639123456789")
- **Value**: Dictionary containing:
  - `messages`: List of SMSMessage objects
  - `timer_task`: asyncio.Task for 60-second timeout

#### 2. **Webhook Processing** (lines 368-475)
When a message arrives:
1. **Deduplication**: Check if GUID was already processed (provider retries)
2. **First message from sender?**
   - YES → Create new buffer, schedule 60-sec timeout
   - NO → Add to existing buffer
3. **Return 200 immediately** (webhook requirement)

Log example:
```
CONSOLIDATION STARTED | From: +639123456789 | Message 1 buffered, waiting 60s for more...
CONSOLIDATION UPDATE | From: +639123456789 | Message 2 buffered, total messages: 2
CONSOLIDATION UPDATE | From: +639123456789 | Message 3 buffered, total messages: 3
```

#### 3. **Consolidation Timeout Handler** (lines 536-576)
Waits 60 seconds, then processes all buffered messages:
```python
async def _consolidation_timeout_handler(phone_number: str, background_tasks: BackgroundTasks)
```

After timeout expires:
- Retrieves all buffered messages for that sender
- Enqueues `process_incoming_sms_batch()` for consolidated processing

#### 4. **Batch Processing** (lines 579-682)
Processes multiple messages as ONE unit:
```python
async def process_incoming_sms_batch(phone_number: str, messages: List[SMSMessage])
```

**Process:**
1. Log all received messages with indices
2. **Consolidate texts**: Join all messages with newlines
3. **Classify ONCE**: Send combined text to OpenAI/fallback
4. **Send ONE auto-reply**: Single response for entire batch

Example log:
```
BATCH RECEIVED | From: 09123456789 | Count: 3
  └─ Message 1/3 | GUID: msg-001 | Text: "Yes"
  └─ Message 2/3 | GUID: msg-002 | Text: "I can help"
  └─ Message 3/3 | GUID: msg-003 | Text: "thanks"
Combined text for classification: Yes\nI can help\nthanks
CONSOLIDATED CLASSIFICATION ✓ AGREE | From: 09123456789 | Method: OpenAI | Messages: 3
AUTO-REPLY SENT (batch) | To: 09123456789 | Messages: 3 | "Thanks for confirming! See you soon."
BATCH PROCESSING COMPLETE | From: 09123456789 | Result: AGREE | Messages: 3
```

---

## Benefits

✅ **Reduced API Calls**: Multiple messages classified in ONE OpenAI call instead of 3  
✅ **Accurate Context**: Classification considers full conversation flow  
✅ **Fewer Auto-Replies**: One reply per conversation, not per message  
✅ **Better UX**: Recipients don't get spam with multiple replies  
✅ **Provider-Friendly**: Consolidation doesn't violate webhook response time requirements  

---

## Configuration

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `SMS_AUTO_REPLY_ENABLED` | `false` | Enable/disable auto-replies for batches |
| `SMS_AUTO_REPLY_TEXT` | Smart default | Custom auto-reply message |
| `CONSOLIDATION_WINDOW` | `60` | Seconds to wait before processing (hardcoded) |

### To Adjust Consolidation Window

Edit line 120 in `sms_sync_server.py`:
```python
CONSOLIDATION_WINDOW = 60  # Change this to your desired seconds
```

---

## Thread Safety

All shared state is protected by locks:

| Resource | Lock | Protection |
|----------|------|-----------|
| `_processed_message_guids` | `_guid_lock` | Deduplication cache |
| `_sender_message_buffer` | `_buffer_lock` | Message consolidation buffer |
| `sms_sender` | `sms_sender_lock` | SMS API client access |

---

## Edge Cases Handled

### 1. **Single Message (No Consolidation)**
```
Message from +639123456789 arrives
→ Timer waits 60 seconds with no additional messages
→ Processes single message normally
→ Result: Same as before, just delayed 60 seconds
```

### 2. **Provider Retries (Duplicate GUIDs)**
```
Same message retried by provider with same GUID
→ Deduplication check catches it
→ Message ignored, not added to buffer
→ Result: No duplicate processing
```

### 3. **Multiple Senders**
```
Message from +639123456789 AND +639987654321 arrive simultaneously
→ Each sender gets independent 60-second window
→ Buffers processed separately
→ Result: Fully parallel, no interference
```

### 4. **Auto-Reply Disabled**
```
SMS_AUTO_REPLY_ENABLED = false
→ Batch processed normally
→ Classification still happens
→ No auto-reply sent
→ Result: Messages are consolidated but no reply
```

---

## Testing Recommendations

### Manual Test 1: Send 3 Quick Messages
1. Send message 1 from +639123456789
2. Wait 2 seconds
3. Send message 2 from +639123456789
4. Wait 2 seconds
5. Send message 3 from +639123456789
6. Wait 60 seconds
7. **Expected**: All 3 classified together, ONE auto-reply sent

### Manual Test 2: Two Different Senders
1. Send message from +639123456789
2. Send message from +639987654321
3. Wait 60 seconds
4. **Expected**: Two separate batches, two classifications, two auto-replies

### Manual Test 3: Single Message
1. Send one message from +639123456789
2. Wait 60 seconds
3. **Expected**: Single message processed normally

### Manual Test 4: Check Logs
```bash
# Watch for consolidation messages
grep "CONSOLIDATION" app.log

# Expected sequence:
# CONSOLIDATION STARTED → CONSOLIDATION UPDATE → CONSOLIDATION TIMEOUT → BATCH RECEIVED
```

---

## Performance Impact

| Scenario | Before | After |
|----------|--------|-------|
| Single message | Immediate | +60 sec delay |
| 3 messages from same sender | 3 API calls + 3 replies | 1 API call + 1 reply |
| 10 messages in 60 sec | 10 API calls | 1 API call |
| Multiple senders | Sequential | Parallel (independent) |

**Latency Trade-off**: Processing is delayed by up to 60 seconds to achieve consolidation benefits. This is acceptable because:
- Webhooks return immediately (within 5ms)
- Background processing is non-blocking
- Auto-replies are sent once instead of multiple times

---

## Troubleshooting

### Messages Not Being Consolidated?
1. Check if `CONSOLIDATION_WINDOW = 60` is set correctly
2. Verify sender phone numbers are identical (including country code)
3. Check logs for "CONSOLIDATION STARTED" message
4. Ensure no exceptions are cancelling the timer

### Auto-Replies Sent Individually?
1. Verify `SMS_AUTO_REPLY_ENABLED = "1"` or `"true"`
2. Check logs for "AUTO-REPLY SENT (batch)"
3. If you see individual "AUTO-REPLY SENT", something is forcing single-message processing

### Duplicate Messages in Batch?
1. This shouldn't happen - check for GUID collisions
2. Verify your SMS provider isn't sending true duplicates
3. Check logs for "DUPLICATE IGNORED"

---

## Future Enhancements

- [ ] Make `CONSOLIDATION_WINDOW` configurable via environment variable
- [ ] Add database logging for audit trail of consolidated batches
- [ ] Implement smart consolidation (group by intent, not just time)
- [ ] Add per-sender consolidation preferences
- [ ] Implement message history retrieval for long conversations
- [ ] Add metrics for consolidation ratio (messages → batches)

---

## Code Changes Summary

**Files Modified:**
- `api/routes/sms_sync_server.py`

**New Functions:**
1. `_get_sender_buffer(phone_number)` - Retrieve buffered messages
2. `_has_pending_messages(phone_number)` - Check if buffer exists
3. `_reset_consolidation_cache()` - Clear all buffers (testing)
4. `_consolidation_timeout_handler()` - Handle 60-second timeout
5. `process_incoming_sms_batch()` - Process consolidated batch

**Modified Functions:**
1. `receive_sms_webhook()` - Implement consolidation logic
2. `process_incoming_sms()` - Deprecated (kept for compatibility)

**New Global State:**
1. `_sender_message_buffer` - Per-sender message queue
2. `_buffer_lock` - Thread-safe access control
3. `CONSOLIDATION_WINDOW` - 60-second window

---

## Questions?

For issues or clarifications, refer to the consolidated logging format which clearly shows each stage of the consolidation process.
