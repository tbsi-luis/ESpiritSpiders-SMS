# Testing Guide: Message Consolidation Feature

## Quick Start Testing

### Test 1: Single Message (Baseline)
**Objective**: Verify single messages are processed normally after 60-second wait

**Steps**:
1. Send a message from your test phone to the webhook
2. Wait 60 seconds
3. Check logs for consolidation sequence

**Expected Logs**:
```
CONSOLIDATION STARTED | From: +639123456789 | Message 1 buffered, waiting 60s for more...
... 60 seconds pass ...
CONSOLIDATION TIMEOUT | From: +639123456789 | Processing 1 buffered message(s)
BATCH RECEIVED | From: 09123456789 | Count: 1
CONSOLIDATED CLASSIFICATION ✓ AGREE | From: 09123456789 | Messages: 1
BATCH PROCESSING COMPLETE | From: 09123456789 | Result: AGREE | Messages: 1
```

**Pass Criteria**: ✅ Single message processed after 60 seconds

---

### Test 2: Rapid Fire Messages (Core Feature)
**Objective**: Verify messages from same sender are consolidated

**Steps**:
1. Send 3 messages in rapid succession (2-3 seconds apart) from same number
   - Message 1: "Yes"
   - Message 2: "I can help"
   - Message 3: "Thank you"
2. Wait 60 seconds
3. Check logs and verify only ONE auto-reply received

**Expected Logs**:
```
CONSOLIDATION STARTED | From: +639123456789 | Message 1 buffered, waiting 60s for more...
CONSOLIDATION UPDATE | From: +639123456789 | Message 2 buffered, total messages: 2
CONSOLIDATION UPDATE | From: +639123456789 | Message 3 buffered, total messages: 3
... 57 seconds pass ...
CONSOLIDATION TIMEOUT | From: +639123456789 | Processing 3 buffered message(s)
BATCH RECEIVED | From: 09123456789 | Count: 3
  └─ Message 1/3 | GUID: msg-001 | Text: "Yes"
  └─ Message 2/3 | GUID: msg-002 | Text: "I can help"
  └─ Message 3/3 | GUID: msg-003 | Text: "Thank you"
Combined text for classification: Yes\nI can help\nThank you
CONSOLIDATED CLASSIFICATION ✓ AGREE | From: 09123456789 | Method: OpenAI | Messages: 3
AUTO-REPLY SENT (batch) | To: +639123456789 | Messages: 3 | "Thanks for confirming! See you soon."
BATCH PROCESSING COMPLETE | From: 09123456789 | Result: AGREE | Messages: 3
```

**Expected SMS Received**:
```
User sends: "Yes"
User sends: "I can help"
User sends: "Thank you"
... 60 seconds later ...
Auto-reply received: "Thanks for confirming! See you soon." (ONLY ONE!)
```

**Pass Criteria**: 
- ✅ All 3 messages buffered
- ✅ Only 1 classification call
- ✅ Only 1 auto-reply sent (not 3)
- ✅ Classification considers all messages

---

### Test 3: Multiple Senders (Isolation)
**Objective**: Verify messages from different senders are processed independently

**Steps**:
1. Send message from Phone A (+639111111111): "Yes"
2. Send message from Phone B (+639222222222): "No"
3. Wait 60 seconds
4. Verify two separate batches processed

**Expected Logs**:
```
CONSOLIDATION STARTED | From: +639111111111 | Message 1 buffered, waiting 60s for more...
CONSOLIDATION STARTED | From: +639222222222 | Message 1 buffered, waiting 60s for more...
... 60 seconds pass ...
CONSOLIDATION TIMEOUT | From: +639111111111 | Processing 1 buffered message(s)
CONSOLIDATION TIMEOUT | From: +639222222222 | Processing 1 buffered message(s)
BATCH RECEIVED | From: 09111111111 | Count: 1
BATCH RECEIVED | From: 09222222222 | Count: 1
CONSOLIDATED CLASSIFICATION ✓ AGREE | From: 09111111111 | Messages: 1
CONSOLIDATED CLASSIFICATION ✗ NOT AGREE | From: 09222222222 | Messages: 1
AUTO-REPLY SENT (batch) | To: +639111111111 | Messages: 1 | ...
AUTO-REPLY SENT (batch) | To: +639222222222 | Messages: 1 | ...
```

**Pass Criteria**:
- ✅ Both messages processed in separate batches
- ✅ Classifications independent
- ✅ 2 auto-replies sent (one to each)

---

### Test 4: Duplicate Prevention (Deduplication)
**Objective**: Verify duplicate GUIDs are ignored

**Steps**:
1. Send message from Phone A: "Yes" (GUID: msg-001)
2. Immediately simulate provider retry with same GUID: msg-001
3. Wait 60 seconds
4. Verify only ONE message in batch

**Expected Logs**:
```
CONSOLIDATION STARTED | From: +639123456789 | Message 1 buffered, waiting 60s for more...
DUPLICATE IGNORED | GUID: msg-001 | From: +639123456789
... 60 seconds pass ...
CONSOLIDATION TIMEOUT | From: +639123456789 | Processing 1 buffered message(s)
BATCH RECEIVED | From: 09123456789 | Count: 1
```

**Pass Criteria**:
- ✅ Duplicate GUID ignored
- ✅ Only 1 message in batch (not 2)
- ✅ Log shows "DUPLICATE IGNORED"

---

### Test 5: Auto-Reply Disabled
**Objective**: Verify consolidation works with auto-replies disabled

**Steps**:
1. Set environment variable: `SMS_AUTO_REPLY_ENABLED=false`
2. Send 2 messages from same sender
3. Wait 60 seconds
4. Verify batch processed but NO auto-reply

**Expected Logs**:
```
CONSOLIDATION STARTED | From: +639123456789 | Message 1 buffered, waiting 60s for more...
CONSOLIDATION UPDATE | From: +639123456789 | Message 2 buffered, total messages: 2
... 60 seconds pass ...
BATCH RECEIVED | From: 09123456789 | Count: 2
CONSOLIDATED CLASSIFICATION ✓ AGREE | From: 09123456789 | Messages: 2
BATCH PROCESSING COMPLETE | From: 09123456789 | Result: AGREE | Messages: 2
```

**Expected SMS**:
```
NO auto-reply received ✓
```

**Pass Criteria**:
- ✅ Batch processed normally
- ✅ NO auto-reply sent
- ✅ No "AUTO-REPLY SENT" in logs

---

## Advanced Testing

### Test 6: Long Consolidation Window (5+ messages)
**Objective**: Verify system handles many messages in one batch

**Steps**:
1. Write a script to send 10 messages from same sender
2. Space them 3-5 seconds apart over 30 seconds
3. Wait 60 seconds from first message
4. Verify all 10 messages in one batch

**Expected Result**:
```
BATCH RECEIVED | From: 09123456789 | Count: 10
  └─ Message 1/10 | GUID: msg-001 | Text: "..."
  └─ Message 2/10 | GUID: msg-002 | Text: "..."
  ... (8 more) ...
  └─ Message 10/10 | GUID: msg-010 | Text: "..."
CONSOLIDATED CLASSIFICATION ✓ AGREE | ... | Messages: 10
```

**Pass Criteria**: ✅ All 10 messages in single batch

---

### Test 7: Edge Case - Messages at 59s and 61s
**Objective**: Verify timer behavior at boundaries

**Steps**:
1. Send message 1 from Phone A at T=0
2. Send message 2 from Phone A at T=59 (just before timeout)
3. Send message 3 from Phone A at T=61 (just after timeout would expire)
4. Observe consolidation behavior

**Expected Behavior**:
- Message 1 & 2 should be in same batch (T=59 is within window)
- Message 3 might start a new batch OR wait for 60s from message 2
- Logs will show the exact behavior

**Log Analysis**:
```
T=0    CONSOLIDATION STARTED (timer for msg-1)
T=59   CONSOLIDATION UPDATE (msg-2 added to same batch)
T=59-120  Wait for timeout...
T=120  BATCH RECEIVED | Count: 2 (msg-1 and msg-2)
T=120  CONSOLIDATION STARTED (timer for msg-3)
T=180  BATCH RECEIVED | Count: 1 (msg-3)
```

**Pass Criteria**: ✅ Messages consolidate correctly based on timing

---

### Test 8: Webhook Response Time
**Objective**: Verify webhook returns immediately (<100ms)

**Steps**:
1. Send message and measure webhook response time
2. Verify returns within 100ms
3. Check that consolidation doesn't delay webhook response

**Measurement**:
```bash
curl -w "@curl-format.txt" -X POST http://localhost:8000/api/webhook/sms-received \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2025-01-20",
    "hour": "10:15:00",
    "time_received": "2025-01-20 10:14:50",
    "message": "Test",
    "number": "+639123456789",
    "guid": "test-001"
  }'
```

**Expected Result**: Response time < 100ms

**Pass Criteria**: ✅ Webhook responds quickly despite consolidation setup

---

## Log Verification Checklist

Use these grep commands to verify consolidation is working:

```bash
# Check consolidation started messages
grep "CONSOLIDATION STARTED" app.log

# Count how many batches were processed
grep "BATCH RECEIVED" app.log | wc -l

# Verify classifications
grep "CONSOLIDATED CLASSIFICATION" app.log

# Check auto-replies
grep "AUTO-REPLY SENT" app.log

# Look for any errors
grep "PROCESSING FAILED" app.log

# Timeline analysis
grep "From: 09123456789" app.log | head -20
```

---

## Performance Testing

### Benchmark: API Call Reduction

**Setup**:
1. Send 100 messages from a single phone number over 60 seconds
2. Measure OpenAI API calls made
3. Compare to old implementation (100 calls vs 1 call)

**Expected Result**:
```
BEFORE (old code): ~100 OpenAI API calls
AFTER (new code):  ~1 OpenAI API call (up to 100x reduction!)
```

**Script** (Python):
```python
import requests
import time

phone = "+639123456789"
for i in range(100):
    requests.post("http://localhost:8000/api/webhook/sms-received", json={
        "date": "2025-01-20",
        "hour": f"{10:02d}:15:00",
        "time_received": "2025-01-20 10:14:50",
        "message": f"Message {i+1}",
        "number": phone,
        "guid": f"perf-{i+1:03d}"
    })
    time.sleep(0.6)  # Send one every 600ms

# Wait 60 seconds for consolidation to complete
time.sleep(65)

# Check logs to count API calls
```

---

## Troubleshooting Test Failures

### Problem: Messages not consolidating
**Check**:
- Are phone numbers exactly identical (including country code)?
- Has 60 seconds actually passed?
- Are messages arriving before timeout cancels?

**Debug**:
```bash
# Find consolidation messages for specific number
grep "09123456789" app.log | grep "CONSOLIDATION"
```

---

### Problem: Multiple auto-replies sent
**Check**:
- Is `SMS_AUTO_REPLY_ENABLED` set to `true`?
- Are messages from different senders (creating separate batches)?
- Is the timer being cancelled and reset?

**Debug**:
```bash
# Check auto-reply count per number
grep "09123456789" app.log | grep "AUTO-REPLY"
```

---

### Problem: Webhook response slow
**Check**:
- Is consolidation logic blocking webhook response?
- Are background tasks properly non-blocking?

**Debug**:
```bash
# Measure webhook response time
curl -w "\n%{time_total}s\n" -X POST http://localhost:8000/api/webhook/sms-received ...
```

---

## Automation Testing Script

### Python Test Suite
```python
import requests
import time
import json

BASE_URL = "http://localhost:8000/api"
PHONE_A = "+639111111111"
PHONE_B = "+639222222222"

def send_sms(phone, message, guid):
    """Send SMS via webhook"""
    payload = {
        "date": "2025-01-20",
        "hour": "10:15:00",
        "time_received": "2025-01-20 10:14:50",
        "message": message,
        "number": phone,
        "guid": guid
    }
    response = requests.post(
        f"{BASE_URL}/webhook/sms-received",
        json=payload,
        timeout=5
    )
    return response.status_code == 200

def test_rapid_fire():
    """Test rapid fire messages from same sender"""
    print("Test: Rapid fire messages...")
    for i in range(3):
        send_sms(PHONE_A, f"Message {i+1}", f"test-{i+1}")
        time.sleep(2)
    print("✓ Sent 3 messages")
    time.sleep(60)
    print("✓ Consolidation completed")

def test_multiple_senders():
    """Test messages from different senders"""
    print("Test: Multiple senders...")
    send_sms(PHONE_A, "From A", "sender-a-1")
    send_sms(PHONE_B, "From B", "sender-b-1")
    print("✓ Sent from 2 senders")
    time.sleep(60)
    print("✓ Consolidation completed")

# Run tests
if __name__ == "__main__":
    test_rapid_fire()
    test_multiple_senders()
    print("\n✓ All tests completed!")
```

---

## Success Criteria Summary

| Test | Expected | Actual |
|------|----------|--------|
| Single message | Process after 60s | ⭕ |
| 3 rapid messages | 1 batch, 1 classification, 1 reply | ⭕ |
| Different senders | 2 independent batches | ⭕ |
| Duplicate GUID | Ignored (only 1 in batch) | ⭕ |
| Auto-reply disabled | Batch processed, no reply | ⭕ |
| 10+ messages | All in single batch | ⭕ |
| Webhook response | < 100ms | ⭕ |
| API call reduction | 1 call instead of many | ⭕ |

Fill in ⭕ with ✅ (pass) or ❌ (fail) during testing.

---

## Regression Testing

After deploying consolidation, test these scenarios to ensure nothing broke:

1. **Old single-message behavior**: Still works ✅
2. **Webhook endpoint**: Still accepts messages ✅
3. **OpenAI classification**: Still works ✅
4. **Rule-based fallback**: Still works ✅
5. **Auto-reply when enabled**: Still sends (just once per batch) ✅
6. **Error handling**: Exceptions still caught ✅
7. **Database logging**: Still logs correctly ✅
8. **Metrics/monitoring**: Still tracks events ✅
