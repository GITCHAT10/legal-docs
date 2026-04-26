# IMOXON LOGISTICS ENGINE

## Overview
The iMOXON Logistics Engine is the execution layer that connects global supplier orders to local island delivery. It governs the end-to-end lifecycle of goods entering the Maldives, from international dispatch to proof-of-delivery (POD) and financial settlement.

## Core Flow (RC1 Production Ready)
1. **Shipment Creation**: Initiated by verified suppliers after PO issuance.
2. **International Dispatch**: Movement from origin to Maldives.
3. **Clearance Operating Engine**:
   - **PRECHECK**: Cargo filter for prohibited/restricted items.
   - **DECLARE**: Submission of Goods Declaration to ASYCUDA.
   - **PAY-DUTY**: Wallet-to-MCS customs payment with dual approval.
   - **RELEASE**: Broker confirmation of MCS release status.
   - **GATE-OUT**: Physical exit from MPL; triggers Skygodown intake.
4. **Skygodown Intake**: Goods received at the warehouse and registered as Lots.
5. **Allocation**: Goods allocated to specific resorts or buyers based on demand.
6. **Manifest & Transport**: Grouping allocations into delivery manifests and assigning verified UT transport.
7. **Islands Delivery**: Scan-based handoff (LOAD/UNLOAD) and recipient confirmation.
8. **Settlement**: Variance-checked release of funds governed by FCE.

## Business Rules
- **Fail-Closed**: All state transitions require `ExecutionGuard` authorization.
- **Traceability**: Every lifecycle event writes a SHADOW audit entry.
- **Variance Control**: Discrepancies above 2% trigger disputes and block payment settlement.
- **Offline Mode**: Edge scans (LOAD/UNLOAD) support local queueing and idempotent replay.
