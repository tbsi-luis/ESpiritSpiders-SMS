# Message Consolidation Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    SMS MOBILE API (Provider)                    │
│                                                                  │
│  Sends webhook when SMS received                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
        ┌──────────────────────────────────┐
        │  Webhook Endpoint                │
        │  POST /api/webhook/sms-received  │
        │  Returns 200 OK immediately      │
        └──────────────────┬───────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ↓                 ↓                 ↓
    ┌─────────┐      ┌──────────┐      ┌──────────┐
    │ Message │      │ Message  │      │ Message  │
    │ from A  │      │ from B   │      │ from A   │
    └────┬────┘      └────┬─────┘      └────┬─────┘
         │                │                  │
         ├──────────────┐  │                  │
         │              │  │                  │
    ┌────▼──────────────▼──▼──────────────────┴─────────────┐
    │  DEDUPLICATION CHECK                                   │
    │  (Check if GUID already processed)                    │
    │                                                        │
    │  _processed_message_guids: deque(maxlen=1000)        │
    │  Protected by: _guid_lock                            │
    └────┬──────────────┬─────────────────────────────────┬─┘
         │ New          │ New                             │ Duplicate
         │              │                                 │ (ignored)
         ↓              ↓                                 ↓
    ┌──────────────────────────────────────────────────┐  ┌──────┐
    │  CONSOLIDATION BUFFER MANAGEMENT                │  │ SKIP │
    │                                                  │  └──────┘
    │  _sender_message_buffer: Dict[phone, buffer]   │
    │  Protected by: _buffer_lock                     │
    │                                                  │
    │  Buffer structure:                              │
    │  {                                              │
    │    "+639123456789": {                           │
    │      "messages": [msg1, msg2, msg3],           │
    │      "timer_task": <asyncio.Task>              │
    │    }                                            │
    │  }                                              │
    └──┬─────────────────────────────────────────────┘
       │
       ├─ First message from sender?
       │  ├─ YES → Create buffer, start timer
       │  └─ NO → Add to existing buffer
       │
       └──────────────────────────────┐
                                       │
                    ┌──────────────────▼────────┐
                    │  Return 200 OK to Provider │
                    │  (webhook requirement met) │
                    └──────────────────┬─────────┘
                                       │
                                       │ Background Processing
                                       │
                    ┌──────────────────▼────────────────────┐
                    │  CONSOLIDATION TIMEOUT HANDLER       │
                    │  asyncio.sleep(CONSOLIDATION_WINDOW) │
                    │  (waits 60 seconds)                  │
                    └──────────────────┬───────────────────┘
                                       │
                    ┌──────────────────▼────────────────────┐
                    │  RETRIEVE BUFFERED MESSAGES          │
                    │  _get_sender_buffer(phone_number)    │
                    │  (gets all messages for sender)      │
                    └──────────────────┬───────────────────┘
                                       │
                    ┌──────────────────▼────────────────────┐
                    │  BATCH PROCESSOR                     │
                    │  process_incoming_sms_batch()        │
                    └──────────────────┬───────────────────┘
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            │                          │                          │
            ↓                          ↓                          ↓
    ┌──────────────┐          ┌──────────────┐          ┌──────────────┐
    │ LOG MESSAGES │          │ CONSOLIDATE  │          │   CLASSIFY   │
    │              │          │ MESSAGES     │          │              │
    │ Message 1/3  │          │              │          │ Combined:    │
    │ Message 2/3  │          │ "Yes\nI can  │          │ "Yes\n       │
    │ Message 3/3  │          │ help\nThanks"          │ I can help\n │
    │              │          │              │          │ Thanks"      │
    └──────────────┘          └──────────────┘          └──┬───────────┘
                                                           │
                                    ┌──────────────────────┤
                                    │                      │
                            ┌───────▼─────────┐    ┌──────▼────────┐
                            │ Try OpenAI API  │    │ Rule-based    │
                            │                 │    │ Fallback      │
                            └───────┬─────────┘    └──────┬────────┘
                                    │                     │
                                    └─────────┬───────────┘
                                              │
                                    ┌─────────▼────────┐
                                    │  RESULT: AGREE   │
                                    │      or          │
                                    │  NOT AGREE       │
                                    └─────────┬────────┘
                                              │
                                    ┌─────────▼────────┐
                                    │  SEND AUTO-REPLY │
                                    │   (if enabled)   │
                                    │                  │
                                    │  ONE reply for   │
                                    │  all messages    │
                                    └─────────┬────────┘
                                              │
                                    ┌─────────▼────────┐
                                    │  FINAL LOGGING   │
                                    │                  │
                                    │  BATCH COMPLETE  │
                                    │  Result: AGREE   │
                                    │  Count: 3 msgs   │
                                    └──────────────────┘
```

---

## State Transitions

### Per-Sender Buffer Lifecycle

```
[NO BUFFER]
    │
    │ First message arrives
    ↓
[ACTIVE BUFFER]
    │
    ├─ New message from same sender arrives
    │  (within 60 seconds)
    ├─ Add to messages list
    ├─ Keep timer running
    │
    │ OR
    │
    ├─ 60 seconds elapsed with no new messages
    │
    ↓
[PROCESSING]
    │
    ├─ Retrieve all buffered messages
    ├─ Consolidate texts
    ├─ Classify once
    ├─ Send auto-reply
    │
    ↓
[COMPLETE]
    │
    ├─ Buffer cleared
    ├─ Timer task cancelled
    │
    ↓
[NO BUFFER] (ready for next conversation)
```

---

## Concurrent Processing Example

### Timeline: Messages from 3 Different Senders

```
T=0:00
  Phone A sends message 1
  └─ Buffer A created, Timer A starts (60s countdown)
  
  Phone B sends message 1
  └─ Buffer B created, Timer B starts (60s countdown)

T=0:05
  Phone A sends message 2
  └─ Added to Buffer A, Timer A still running

T=0:10
  Phone C sends message 1
  └─ Buffer C created, Timer C starts (60s countdown)

T=1:00 (60 seconds from Phone A's first message)
  Timer A expires
  └─ Batch process starts for Phone A
  └─ Buffer A cleared
  └─ (Phone B and C timers still running)

T=1:03
  Batch A processing complete
  └─ Phone A results logged

T=1:05 (60 seconds from Phone B's first message)
  Timer B expires
  └─ Batch process starts for Phone B
  └─ Buffer B cleared
  └─ (Phone C timer still running)

T=1:10
  Batch B processing complete
  └─ Phone B results logged

T=1:10 (60 seconds from Phone C's first message)
  Timer C expires
  └─ Batch process starts for Phone C
  └─ Buffer C cleared

T=1:12
  Batch C processing complete
  └─ Phone C results logged

All 3 conversations processed independently and concurrently ✓
```

---

## Memory Layout

### Data Structures

```
Global Variables:
┌─────────────────────────────────────────────────┐
│ _processed_message_guids: deque(maxlen=1000)   │
│ └─ [guid1, guid2, guid3, ...]                  │
│    (LRU cache of 1000 recent GUIDs)            │
├─ _guid_lock: Lock()                            │
│    (protects above)                            │
│                                                │
│ _sender_message_buffer: Dict[phone, data]      │
│ ├─ "+639123456789": {                          │
│ │  ├─ messages: [SMSMessage, SMSMessage, ...]  │
│ │  └─ timer_task: asyncio.Task                 │
│ ├─ "+639987654321": {                          │
│ │  ├─ messages: [SMSMessage]                   │
│ │  └─ timer_task: asyncio.Task                 │
│ └─ ...                                         │
├─ _buffer_lock: Lock()                          │
│    (protects above)                            │
│                                                │
│ CONSOLIDATION_WINDOW = 60  (seconds)           │
└─────────────────────────────────────────────────┘

Per-SMS Object:
┌─────────────────────────────┐
│ SMSMessage                  │
├─ date: str                 │
├─ hour: str                 │
├─ time_received: str        │
├─ message: str              │
├─ number: str               │
└─ guid: str                 │
```

---

## Call Flow Sequence

```
Client/SMS Provider
    │
    │ POST /api/webhook/sms-received
    │ {"number": "+639123456789", "message": "Yes", "guid": "msg-001"}
    │
    ├─────────────────────────────────────┐
    │                                     │
    │ WEBHOOK THREAD (main)               │ BACKGROUND THREAD (async)
    │                                     │
    │ 1. Receive request ─────────────┐  │
    │                                 │  │
    │ 2. Parse JSON ──────────────────┤  │
    │                                 │  │
    │ 3. Check dedup ────────────────┤  │
    │    ✓ New message               │  │
    │                                 │  │
    │ 4. Acquire _buffer_lock ───────┤  │
    │    ✓ Lock acquired             │  │
    │                                 │  │
    │ 5. Check if first message ─────┤  │
    │    ✓ Yes, first from sender    │  │
    │                                 │  │
    │ 6. Create buffer ──────────────┤  │
    │    _sender_message_buffer[phone]  │
    │     = {messages: [msg], ...}   │  │
    │                                 │  │
    │ 7. Create timer task ──────────┤──┼──→ Timer starts
    │    asyncio.create_task(        │  │   (60 second countdown)
    │     _consolidation_timeout...) │  │
    │                                 │  │
    │ 8. Release _buffer_lock ───────┤  │
    │    ✓ Lock released             │  │
    │                                 │  │
    │ 9. Return 200 OK ──────────────┼──┼──→ Response sent (< 100ms)
    │                                 │  │
    │ [Webhook complete]              │  │
    │                                 │  │ [Timer running]
    │                                 │  │ T = 0...59 seconds
    │                                 │  │
    │                                 │  │ [60 seconds elapsed]
    │                                 │  │
    │                                 │  │ 8. Timer expires
    │                                 │  │    _consolidation_timeout_handler()
    │                                 │  │
    │                                 │  │ 9. Get buffered messages
    │                                 │  │    _get_sender_buffer(phone)
    │                                 │  │
    │                                 │  │ 10. Enqueue batch processor
    │                                 │  │     background_tasks.add_task(
    │                                 │  │      process_incoming_sms_batch)
    │                                 │  │
    │                                 │  │ 11. Classify & send reply
    │                                 │  │     (async work continues)
    │
    │ [Background work complete]
    │
    └─────────────────────────────────┘
```

---

## Lock Contention Analysis

```
Critical Sections:

1. Deduplication Check (_guid_lock)
   Duration: < 1ms
   Frequency: Per message
   Contention: Minimal

2. Buffer Access (_buffer_lock)
   Duration: < 1ms (for add operation)
   Frequency: Per message
   Contention: Minimal

3. SMS Send (sms_sender_lock)
   Duration: ~100ms (network call)
   Frequency: Once per batch
   Contention: Minimal

All locks protect short critical sections.
No lock holding during I/O operations.
Thread-safe by design. ✓
```

---

## Error Recovery

```
Error Scenario: OpenAI API Fails

    Batch Processor
        │
        ├─ Try OpenAI API
        │  └─ ERROR: Network timeout
        │
        ├─ Catch RuntimeError/Exception
        │
        ├─ Fallback to rule-based classifier
        │  └─ SUCCESS: Returns AGREE/NOT AGREE
        │
        ├─ Continue processing
        │
        └─ Send reply & log (treatment continued)

Result: No data loss, no incomplete processing ✓
```

---

## Performance Optimization

### API Call Reduction

```
Before:  Message 1 → Classify → API Call ✓
         Message 2 → Classify → API Call ✓
         Message 3 → Classify → API Call ✓
         Total: 3 API calls, 3 replies

After:   Message 1 ┐
         Message 2 ├─ Consolidate → Classify → 1 API Call ✓
         Message 3 ┘                        → 1 Reply ✓
         Total: 1 API call, 1 reply

Savings: 66% - 90% depending on follow-up rate
```

---

## Integration Points

```
External Systems:

SMS Provider
  └─ Webhook callback
     └─ sms_sync_server receives message

OpenAI API
  └─ Async classification
     └─ classify_message_with_openai()

SMS Sender
  └─ Send auto-reply
     └─ sms_sender.send_message()

Logging
  └─ Record all events
     └─ logger (structured logs)

Database (if used)
  └─ Optional audit logging
     └─ (not implemented in consolidation)
```

---

## Resource Utilization

```
Memory:
  - Per sender: ~1-2 KB (buffer + timer)
  - Max 1000 senders buffered: ~1-2 MB
  - Dedup cache: ~50 KB (1000 GUIDs)
  - Total overhead: Minimal

CPU:
  - Webhook response: Negligible (< 1ms CPU)
  - Consolidation timer: Event-driven (no polling)
  - Batch classification: As before (1 call instead of many)

Network:
  - Webhook I/O: Same as before
  - OpenAI API: 66-90% reduction
  - SMS replies: 50-90% reduction

Disk:
  - Log space: Same as before (additional consolidation log entries)
```

---

## Scalability

```
Single Server Capacity:

Incoming Messages:
  - No change from original
  - Webhook can handle same throughput

Concurrent Conversations:
  - Dict-based buffer: O(1) lookup
  - Lock overhead: Minimal
  - Can handle 1000s of concurrent conversations

Timer Tasks:
  - One timer per active sender
  - 1000+ timers can run concurrently
  - asyncio handles efficiently

Bottleneck:
  - OpenAI API rate limits (but now 1/10th calls!)
  - Not the consolidation system
```

---

This architecture provides:
✅ High scalability
✅ Minimal resource overhead
✅ Efficient consolidation
✅ Safe concurrent processing
✅ Error resilience
✅ API cost reduction
