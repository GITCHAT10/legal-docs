# NEXUS ASI SKY-i OS — RELEASE CANDIDATE 1

## 🏛️ System Configuration
- **Jurisdiction**: Maldives (MV)
- **Service Charge**: 10%
- **TGST**: 17%
- **Green Tax**: $6/pax/night

## 🧠 Intelligence Thresholds
- **Min Intent Score**: 0.90
- **Min Confidence Score**: 0.85

## 🧾 Event Taxonomy
- `nexus.booking.created`
- `nexus.guest.arrival`
- `nexus.payment.received`
- `nexus.emergency.triggered`

## 🛡️ Audit Schema
- **Ledger Type**: SHA-256 Hash Chain
- **Entry Pattern**: `previous_hash + event_type + payload + entry_id → current_hash`
- **Integrity**: Immutable, Append-Only

---
**Build Status**: LOCKED (Release Candidate 1)
**Date**: 2026-04-22
