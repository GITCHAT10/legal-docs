# 🚨 RUNBOOK 001: LEDGER HASH CHAIN BREACH (CRITICAL)

## Symptoms
- Dashboard shows "❌ LEDGER INTEGRITY FAILURE"
- Payouts auto-frozen by Smart Gate.

## Immediate Actions
1. HALT ALL PAYOUTS: `curl -X POST https://gate.bubble.mv/api/v1/emergency/freeze`
2. Isolate Ledger Service.
3. Preserve Evidence (Immutable Snapshot).

## Resolution
1. Identify first mismatch.
2. Restore from last known good hash or backup.
3. Re-verify hash chain linkage.
