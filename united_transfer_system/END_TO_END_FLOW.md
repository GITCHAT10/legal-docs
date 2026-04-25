# End-to-End Flow: United Transfer ASI

This document outlines the sovereign flow from booking to instant payout.

## 1. Booking Phase
- **Partner Request**: Signed API call to `POST /ut/v1/book`.
- **Validation**: Middleware checks `X-UT-Signature` and `AEGIS` context.
- **Atomic Creation**: `Journey` created in `CREATED` state. `SHADOW` intent logged.

## 2. Dispatch Phase
- **Operator Action**: `PUT /ut/v1/journey/{id}/status` -> `CONFIRMED`.
- **Resource Lock**: Vehicle/Crew assigned.

## 3. Pickup (QR1)
- **Physical Handshake**: Passenger scans QR1.
- **Verification**: `ExecutionGuard` verifies `DISPATCHED` state.
- **State Change**: State becomes `PICKED_UP`.

## 4. Movement
- **Telemetry**: GPS updates streamed to `POST /ut/telemetry`.
- **Validation**: Real-world weather/status checked autonomously by `APOLLO`.

## 5. Drop (QR2)
- **Physical Handshake**: Destination scan.
- **Verification**: `ExecutionGuard` verifies `QR1` was completed.
- **State Change**: State becomes `DROPPED` then `COMPLETED`.

## 6. Settlement
- **FCE Integration**: `finalize_invoice` called via signed NEXUS API.
- **Instant Payout**: `release_payout` executed to operator wallet.
- **Final State**: State becomes `PAID`. `SHADOW` result sealed.
