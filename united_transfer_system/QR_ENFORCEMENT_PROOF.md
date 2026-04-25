# QR Enforcement Proof

The "Universal Handshake" protocol ensures that payments are only released after a journey is physically verified through a Dual-QR system.

## Protocol sequence:

1. **QR1 (Pickup Handshake)**:
   - Scanned by passenger/driver at pickup.
   - Updates state from `DISPATCHED` to `PICKED_UP`.
   - Blocked if state is not `DISPATCHED`.

2. **QR2 (Drop Handshake)**:
   - Scanned by passenger/operator at destination.
   - Updates state from `IN_TRANSIT` to `DROPPED`.
   - Blocked if `QR1` was never verified.

3. **Payment Release**:
   - Condition: `QR1_VERIFIED == True` AND `QR2_VERIFIED == True` AND `STATUS == COMPLETED`.
   - Logic: `finalize_invoice()` -> `release_payout()`.
   - **Fail-Closed**: If QR2 is missing, `payout_engine` rejects the request.

## Forensic Proof:
All QR handshakes are logged as individual evidence entries in the `SHADOW` ledger, containing:
- `leg_id`
- `scan_timestamp`
- `gps_coordinates`
- `operator_id`
