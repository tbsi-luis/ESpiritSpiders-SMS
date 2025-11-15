# Deployment Guide: Message Consolidation Feature

## Pre-Deployment Checklist

### Code Review
- [ ] Read `CODE_CHANGES.md` to understand modifications
- [ ] Review `ARCHITECTURE.md` to understand design
- [ ] Check that only `api/routes/sms_sync_server.py` was modified
- [ ] Verify no external dependencies added
- [ ] Confirm backward compatibility maintained

### Local Testing
- [ ] Follow `TESTING_GUIDE.md` Test 1 (Single message)
- [ ] Follow `TESTING_GUIDE.md` Test 2 (Rapid-fire messages)
- [ ] Follow `TESTING_GUIDE.md` Test 3 (Multiple senders)
- [ ] Follow `TESTING_GUIDE.md` Test 4 (Duplicate prevention)
- [ ] Follow `TESTING_GUIDE.md` Test 5 (Auto-reply disabled)
- [ ] Verify logs show consolidation messages
- [ ] Check that no errors are raised

### Configuration Review
- [ ] Environment variables unchanged (backward compatible)
- [ ] No new env vars required
- [ ] Optional: Verify `CONSOLIDATION_WINDOW = 60` is acceptable
- [ ] Optional: Adjust if different value needed

---

## Staging Deployment

### 1. Deploy Code
```bash
# Backup current version
cp api/routes/sms_sync_server.py api/routes/sms_sync_server.py.backup

# Deploy new version
git pull origin main  # or copy new file

# Restart service
systemctl restart your-sms-service
```

### 2. Initial Validation
```bash
# Check service is running
systemctl status your-sms-service

# Check for startup errors
journalctl -u your-sms-service -n 50 -f

# Verify webhook health
curl http://localhost:8000/api/webhook/sms-received -X GET
# Expected: {"status": "ok", ...}
```

### 3. Monitor Logs (First Hour)
```bash
# Watch for consolidation messages
grep "CONSOLIDATION" your-app.log | tail -20

# Watch for errors
grep "ERROR\|FAILED" your-app.log | tail -20

# Verify no exceptions
grep "Exception\|Traceback" your-app.log
```

### 4. Send Test Messages
```bash
# Send 3 test messages rapidly from same number
# Expected logs:
# - CONSOLIDATION STARTED
# - CONSOLIDATION UPDATE (x2)
# - CONSOLIDATION TIMEOUT
# - BATCH RECEIVED (Count: 3)
# - CONSOLIDATED CLASSIFICATION
# - AUTO-REPLY SENT (batch)

# Verify in logs
grep "From: +639123456789" your-app.log | head -20
```

### 5. Verify API Calls
```bash
# Count OpenAI API calls in logs
grep "OpenAI" your-app.log | wc -l

# Should be much fewer than message count
# Example: 3 messages → 1 API call ✓
```

### 6. Check Auto-Replies
```bash
# Verify only 1 reply per batch
grep "AUTO-REPLY SENT" your-app.log

# Should show (batch) and single sender replies
# NOT multiple replies to same number ✓
```

### 7. 24-Hour Staging Test
- [ ] Run production-like traffic for 24 hours
- [ ] Monitor for any issues or errors
- [ ] Collect performance metrics
- [ ] Verify cost reduction
- [ ] Get stakeholder approval

---

## Production Deployment

### Pre-Production Steps
```bash
# Final backup
cp api/routes/sms_sync_server.py api/routes/sms_sync_server.py.backup

# Verify git status
git status  # Should be clean
git diff HEAD  # Should show only sms_sync_server.py changes

# Tag current version
git tag pre-consolidation-rollback
```

### Deployment

**Option 1: Direct Deployment (For small teams)**
```bash
# Pull latest code
git pull origin main

# Restart service
systemctl restart your-sms-service

# Watch logs for 5 minutes
journalctl -u your-sms-service -f | grep -E "CONSOLIDATION|ERROR"
```

**Option 2: Blue-Green Deployment (For critical systems)**
```bash
# 1. Start new service instance (green)
systemctl start your-sms-service-green

# 2. Run health checks
curl http://localhost:8001/api/webhook/sms-received -X GET

# 3. Send test messages to verify
# ... (see test procedures above)

# 4. Switch traffic (update load balancer)
# Point all traffic to green instance

# 5. Monitor for 1 hour
grep "CONSOLIDATION" green-app.log

# 6. Stop old instance (blue)
systemctl stop your-sms-service-blue
```

**Option 3: Canary Deployment (For large systems)**
```bash
# 1. Deploy to 10% of traffic
# ... (configure load balancer)

# 2. Monitor for 1 hour
# Collect metrics: API calls, errors, latency

# 3. If OK, increase to 25%
# Monitor for 1 hour

# 4. If OK, increase to 50%
# Monitor for 1 hour

# 5. If OK, increase to 100%
# Full rollout complete
```

### Post-Deployment Verification

**Immediate (First 5 Minutes)**
```bash
# Service running?
systemctl status your-sms-service
# Expected: active (running)

# No startup errors?
journalctl -u your-sms-service -n 100 | grep ERROR
# Expected: No errors

# Webhook responding?
curl http://localhost:8000/api/webhook/sms-received
# Expected: {"status": "ok", ...}
```

**First Hour**
```bash
# Are messages arriving?
grep "CONSOLIDATION STARTED" your-app.log | wc -l
# Expected: > 0

# Any exceptions?
grep "Exception" your-app.log
# Expected: None

# API calls reduced?
grep "Method: OpenAI\|Method: Rule-based" your-app.log | wc -l
# Expected: Far fewer than message count

# Auto-replies working?
grep "AUTO-REPLY SENT" your-app.log
# Expected: (batch) format with message counts
```

**First 24 Hours**
```bash
# Monitor dashboard for:
- OpenAI API call count (should be 66-90% lower)
- SMS credit usage (should be lower)
- Error rate (should be 0%)
- Response latency (should be unchanged)
- Webhook response time (should be < 100ms)

# Collect logs
grep "CONSOLIDATION\|AUTO-REPLY\|ERROR" your-app.log > consolidation-report.log

# Analyze metrics
tail -100 consolidation-report.log
```

### Metrics to Track

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| OpenAI API calls/day | X | Should be X/10 | -90% |
| SMS credits/day | Y | Should be Y/2 | -50% to -90% |
| Error rate | 0% | 0% | 0% |
| Response latency | < 100ms | < 100ms | Same |
| Processing latency | Immediate | +60s max | Acceptable |
| Auto-reply count/conversation | 3-5 | 1 | Reduced |

---

## Rollback Plan

### Quick Rollback (If Issues Found)

```bash
# Option 1: Immediate rollback
cp api/routes/sms_sync_server.py.backup api/routes/sms_sync_server.py
systemctl restart your-sms-service

# Expected: Service returns to old behavior immediately

# Option 2: Git rollback
git checkout HEAD~1 -- api/routes/sms_sync_server.py
systemctl restart your-sms-service

# Option 3: Tag-based rollback
git checkout pre-consolidation-rollback -- api/routes/sms_sync_server.py
systemctl restart your-sms-service
```

### Rollback Verification
```bash
# Service still running?
systemctl status your-sms-service

# No errors?
journalctl -u your-sms-service -n 50 | grep ERROR

# Webhook responding?
curl http://localhost:8000/api/webhook/sms-received

# Processing messages?
grep "SMS RECEIVED" your-app.log | tail -5
```

---

## Monitoring Commands

### Watch Real-Time Consolidation
```bash
# Terminal 1: Watch consolidation events
tail -f your-app.log | grep "CONSOLIDATION\|BATCH"

# Terminal 2: Watch errors
tail -f your-app.log | grep "ERROR\|FAILED"

# Terminal 3: Watch auto-replies
tail -f your-app.log | grep "AUTO-REPLY"
```

### Daily Metrics Report
```bash
# Create daily report
cat > daily-report.sh << 'EOF'
#!/bin/bash
echo "=== Consolidation Metrics (Last 24h) ==="
echo "Consolidation started events:"
grep "CONSOLIDATION STARTED" your-app.log | tail -100 | wc -l

echo "Batches processed:"
grep "BATCH RECEIVED" your-app.log | tail -100 | wc -l

echo "Average messages per batch:"
grep "BATCH RECEIVED" your-app.log | tail -100 | \
  grep -oP 'Count: \K\d+' | \
  awk '{sum+=$1} END {print sum/NR}'

echo "OpenAI classifications:"
grep "CONSOLIDATED CLASSIFICATION.*OpenAI" your-app.log | tail -100 | wc -l

echo "Rule-based fallbacks:"
grep "CONSOLIDATED CLASSIFICATION.*Rule-based" your-app.log | tail -100 | wc -l

echo "Errors:"
grep "ERROR\|FAILED" your-app.log | tail -100 | wc -l
EOF

chmod +x daily-report.sh
./daily-report.sh
```

---

## Success Indicators

### Within First Hour
- ✅ Service starts without errors
- ✅ Webhook responds to requests
- ✅ Logs show "CONSOLIDATION STARTED" messages
- ✅ Logs show "BATCH RECEIVED" with multiple messages
- ✅ Single "CONSOLIDATED CLASSIFICATION" per batch
- ✅ Single auto-reply per batch

### Within First 24 Hours
- ✅ No unhandled exceptions in logs
- ✅ OpenAI API calls reduced by 66-90%
- ✅ SMS credits used reduced by 50-90%
- ✅ All messages processed correctly
- ✅ Webhook response time unchanged (< 100ms)
- ✅ Cost reduction verified

### Ongoing
- ✅ Error rate remains at 0%
- ✅ Messages consolidated as expected
- ✅ No memory leaks or resource issues
- ✅ Cost savings sustained
- ✅ User satisfaction maintained

---

## Troubleshooting During Deployment

### Issue: Service won't start
**Causes**:
1. Syntax error in code
2. Missing import
3. Port already in use

**Solution**:
```bash
# Check error
journalctl -u your-sms-service -n 50

# Verify syntax
python -m py_compile api/routes/sms_sync_server.py

# Rollback if needed
cp api/routes/sms_sync_server.py.backup api/routes/sms_sync_server.py
systemctl restart your-sms-service
```

### Issue: Messages not consolidating
**Causes**:
1. Phone numbers not identical
2. Messages arriving > 60 seconds apart
3. Service just started (no history yet)

**Solution**:
```bash
# Check phone numbers
grep "CONSOLIDATION" your-app.log | grep "From:"

# Verify timer
grep "CONSOLIDATION STARTED\|CONSOLIDATION TIMEOUT" your-app.log

# Send test messages with identical numbers
```

### Issue: Too many auto-replies
**Causes**:
1. Different senders (creates separate batches)
2. Auto-reply enabled per batch (this is correct!)
3. Service is processing old unprocessed messages

**Solution**:
```bash
# Check if from same sender
grep "AUTO-REPLY SENT" your-app.log | grep "To:"

# Verify consolidation window
grep "CONSOLIDATION" your-app.log | head -20

# Restart service to clear old buffers
systemctl restart your-sms-service
```

### Issue: High memory usage
**Causes**:
1. Buffer not clearing (shouldn't happen)
2. Too many inactive senders

**Solution**:
```bash
# Restart to clear buffers
systemctl restart your-sms-service

# Monitor memory
free -h
systemctl status your-sms-service | grep Memory

# Should be negligible (< 1MB per 1000 active senders)
```

---

## Performance Validation

### Before Consolidation
```bash
# Get baseline metrics (from logs/monitoring)
OpenAI calls/day: 500
SMS credits/day: 500
Cost/day: $5.00
```

### After Consolidation (Day 1)
```bash
# Verify reduction
OpenAI calls/day: ~50 (90% reduction) ✓
SMS credits/day: ~50 (90% reduction) ✓
Cost/day: ~$0.50 (90% reduction) ✓
```

### Success Criteria
- [ ] OpenAI calls reduced by at least 66%
- [ ] SMS credits reduced by at least 50%
- [ ] No increase in error rate
- [ ] Webhook response time unchanged
- [ ] All messages processed correctly

---

## Communication Plan

### Inform Stakeholders
- [ ] **Before deployment**: "We're deploying message consolidation to reduce costs"
- [ ] **After deployment**: "Consolidation deployed. API calls reduced 80%+"
- [ ] **Day 1 report**: Cost savings verified
- [ ] **Week 1 report**: Full metrics and analysis

### User Communication (If Applicable)
- [ ] **Inform users**: "You may notice replies take up to 60 seconds. This is normal."
- [ ] **Explain benefit**: "You'll receive fewer auto-replies (1 instead of 5)"
- [ ] **Provide support**: "If you have issues, contact..."

---

## Post-Deployment Optimization

### Week 1
- [ ] Collect full metrics
- [ ] Analyze consolidation patterns
- [ ] Identify any issues
- [ ] Get team feedback

### Week 2-4
- [ ] Monitor sustained cost reduction
- [ ] Check for any degradation
- [ ] Gather user feedback
- [ ] Plan further optimizations

### Future Enhancements
- [ ] Make consolidation window configurable via env var
- [ ] Add database audit logging
- [ ] Implement smart grouping (by intent)
- [ ] Add per-sender preferences
- [ ] Create consolidation metrics dashboard

---

## Documentation for Team

Create team documentation:

```markdown
# Message Consolidation - Team Guide

## What Changed?
- Messages from same sender arriving within 60 seconds are now consolidated
- Only 1 API call instead of multiple
- Only 1 auto-reply instead of multiple

## How to Monitor
- Watch logs for "CONSOLIDATION" messages
- Check daily metrics (API calls, SMS credits)
- Monitor error logs (should be empty)

## If Something Goes Wrong
1. Check logs: `tail -f your-app.log | grep ERROR`
2. Contact [Tech Lead] for issues
3. Rollback procedure: [link to this document]

## Cost Savings
- Reduced API calls by 80%+
- Reduced SMS credits by 50-90%
- Estimated savings: $X/month

## Questions?
See: [links to documentation files]
```

---

## Sign-Off

### Deployment Approval
- [ ] Code reviewed and approved
- [ ] Tests passed in staging
- [ ] 24-hour staging validation complete
- [ ] Stakeholder approval received
- [ ] Rollback plan documented and tested

### Post-Deployment Approval
- [ ] Metrics verified (API calls reduced)
- [ ] Error rate confirmed at 0%
- [ ] No user complaints reported
- [ ] Cost savings realized
- [ ] Production deployment successful ✅

---

## Helpful Commands

```bash
# Monitor consolidation in real-time
watch "grep 'CONSOLIDATION\|BATCH' your-app.log | tail -10"

# Count messages vs batches
echo "Messages:" $(grep "Message.*GUID:" your-app.log | wc -l)
echo "Batches:" $(grep "BATCH RECEIVED" your-app.log | wc -l)

# API call reduction
echo "OpenAI calls:" $(grep "Method: OpenAI" your-app.log | wc -l)

# Check for errors
grep -i "error\|failed\|exception" your-app.log | head -20

# Generate daily report
grep -E "CONSOLIDATION|BATCH|AUTO-REPLY" your-app.log | tail -100 > report.txt
```

---

## Summary

✅ **Fully documented deployment process**
✅ **Pre-deployment checklist provided**
✅ **Multiple deployment options available**
✅ **Comprehensive monitoring procedures**
✅ **Clear rollback plan**
✅ **Success criteria defined**
✅ **Troubleshooting guide included**

**Ready for production deployment!** 🚀
