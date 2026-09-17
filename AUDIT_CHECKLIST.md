# 🏛️ iMOXON / MNOS — Production Audit Checklist

## 1. AEGIS (Identity Authority)
- [x] All routes protected by `aegis_dome_gate` middleware.
- [x] Mandatory identity headers: `X-MNOS-USER`, `X-MNOS-DEVICE`, `X-MNOS-ROLE`.
- [x] Role-based access control (LOCAL_USER vs. TOURIST_USER) enforced in AEGIS Core.
- [x] Server-side device binding verification implemented.
- [ ] eFaas live integration (currently stubbed).

## 2. FCE (Finance Authority)
- [x] No direct money calculations inside engines; all calls routed to FCE Adapter.
- [x] MIRA-compliant tax rates (8% GGST, 17% TGST) centralized in FCE.
- [x] Payout split logic enforced for Franchise and iSKY HMS.
- [ ] Double-entry ledger integration (Pending in next step).

## 3. SHADOW (Immutable Ledger)
- [x] Every critical action creates a SHADOW entry.
- [x] Genesis block validation and full-chain re-hashing implemented.
- [x] Deepcopy used to prevent payload mutation from breaking integrity.
- [x] No destructive edit paths (update/delete) provided for records.

## 4. EVENTS (Orchestration Authority)
- [x] Side effects (async actions) triggered ONLY after commit/SHADOW log.
- [x] Centralized event taxonomy (ORDER_CREATED, RENT_PAID, etc.).

## 5. Engines & Branding
- [x] All 22+ specialized modules बैठ under iMOXON brand.
- [x] No standalone auth or finance logic in modules.
- [x] Tenancy Act 2021 compliance rules implemented in HOMES.
- [x] Minimalist Aman-style eco-folios for SALA 2026 sustainability.

## ⚠️ Gaps / Action Items
1. Implementation of MIRA-compliant Double-Entry schema.
2. Migration from in-memory storage to persistent DB (PostgreSQL).
3. Live integration with Favara and eFaas production endpoints.
