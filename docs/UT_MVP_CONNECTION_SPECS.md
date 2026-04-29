# 🚤 UT MVP CONNECTION PLAN — PRODUCTION SPEC (Flight → Transfer Continuity)

## Purpose:
Minimal, reliable integration between Flight MVP and UT dispatch: **Flight delayed → UT adjusts → guest informed**.

# 1. CORE LOGIC: THE RESCHEDULE RULE
- Threshold: Delay > 30 minutes.
- Calculation: New Pickup = Actual/Estimated Arrival + 45 minutes buffer.
- Action: Reschedule UT ticket via API.

# 2. CAPACITY CHECK & CACHING
- Lookup in-memory capacity cache before rescheduling.
- Round time to 15-minute buckets.
- If capacity < pax_count, fallback to manual ops.

# 3. MANUAL OPS FALLBACK
- Queue adjustments for manual review if:
    a) No capacity in requested slot.
    b) UT API error.
- Priority: GCCC guests first.

# 4. GUEST NOTIFICATION
- Immediate push notification/SMS after confirmation.
- Format: "Flight [ID] delayed [X]min. Your transfer is now at [HH:MM]."

# 5. SHADOW AUDIT EVENTS
- `UT_MVP_AUTO_ADJUSTED`
- `UT_MVP_MANUAL_OVERRIDE_QUEUED`
- `UT_MVP_MANUAL_OVERRIDE_COMPLETED`
