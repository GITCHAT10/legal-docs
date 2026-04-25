# MIG FINANCE PRODUCTION COMPLIANCE LOCK
**System:** MIG_FINANCE
**Status:** SOVEREIGN_COMPLIANCE_LOCK

## Legal Entity
- **Name:** MALDIVES INTERNATIONAL GROUP PVT LTD
- **TIN:** 1166708
- **Address:** H.THUNIYA, MALE

## 1. Sovereign Tax Engine
- **Service Charge:** 10%
- **TGST:** 17% (Applied to Base + Service Charge subtotal)
- **Rounding:** Banker's Rounding (Round Half Up to 2DP)
- **Currency:** Multi-currency support (USD/MVR) with mandatory FX locking.

## 2. Escrow and Settlements
- **Locking:** Funds are locked on initialization (Purchase Order / Booking).
- **Release:** Release triggered only on verified events (GRN / Journey Completion).
- **Control:** No financial release is permitted without a corresponding SHADOW commit.

## 3. Multi-Sig Governance
- **Requirement:** 2-of-3 multisig approval required for all high-value or manual override actions.
- **Enforcement:** No execution path exists without verified governance approval.

## 4. Audit Integrity
- **Log Level:** MIG_SHADOW_AUDIT_STRICT
- **Traceability:** Mandatory pre-commit intent logging.
- **Chain:** Immutable hash chain with daily forensic anchoring.
