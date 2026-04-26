# UNITED TRANSFER ASI: Open-API Sandbox Manifest

## LOCK TRUST LAYER (v1.0.0)

This Sandbox is governed by the **MIG Identity-Payment-Tax Core**. All transactions are recorded to the **SHADOW Immutable Evidence Chain**.

---

### 1. IDENTITY & AUTHENTICATION
All requests must be signed and include a verified `aegis_id` and `device_id`.
- **eFaas Integration**: Biometric KYC tokens (`DID:TIMESTAMP:SIGNATURE`) must be provided for guest/citizen onboarding.
- **Identity Tiers**:
  - `guest`: Tourism pricing (USD, 10% SC, 17% TGST)
  - `citizen`: Local pricing (MVR, 8% GST)
  - `work_permit`: Specialized pricing (MVR)

---

### 2. CORE ENDPOINTS (REST)

#### POST `/v1/book`
Create multi-leg journeys.
- **Rules**: Must provide a unique `trace_id`.
- **Response**: Returns a `Journey` object with unique `master_voucher_code` for each leg.

#### POST `/v1/handshake`
The Dual-QR verification gate.
- **scan_type**: `pickup` or `dropoff`
- **Rules**:
  - Only `AUTHORIZED_OPERATOR` can perform scans.
  - Handshake expires 48h after scheduled departure.
  - Every successful handshake is committed to the SHADOW ledger.

#### POST `/v1/telemetry`
Real-time GPS telemetry ingestion.
- **Impact**: Used for 'Safe Arrival' verification and instant payout triggers.

---

### 3. FINANCIAL INTEGRITY
- **MIRA Compliance**: System automatically splits GST (8%) or TGST (17%) based on passenger identity.
- **Instant Settlement**: Payments are released to vendor wallets the moment `dropoff` is verified via GPS + QR triangulation.

---

### 4. WEBHOOKS (Event Bus)
Authorized partners can subscribe to:
- `transfer.safe_arrival`: Triggered on QR2 scan verification.
- `transfer.telemetry.update`: Real-time position updates.
- `ledger.shadow_commit`: Immutable audit stubs for all state changes.

---

### 5. SOVEREIGN SAFETY
- **Dynamic Chartering**: Autonomous fleet consolidation based on route density.
- **Autonomous Re-routing**: Weather-aware redirection (Met Office integration).

---
**One App. One API. One Maldives.**
