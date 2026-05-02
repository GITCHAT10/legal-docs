# iMOXON / MNOS: Sovereign Operating System

## Architecture Overview

iMOXON / MNOS is a unified sovereign operating system for island economies. It provides a complete vertical stack for governance, commerce, hospitality, and logistics.

### Core Modules

- **AEGIS**: Identity and hardware device binding authority.
- **MAC EOS**: Governance and business rule validation authority.
- **FCE**: Financial clearing, tax, and settlement authority.
- **SHADOW**: Forensic-grade immutable audit chain.
- **APOLLO**: Offline-first synchronization and edge replay engine.

### Vertical Modules

- **iMOXON.UPOS**: The commerce execution engine.
  - Responsibilities: Checkout, POS, Marketplace Cart, QR Pay, Wallet, Invoices, Refunds, Vendor Payouts, Commissions.
  - **Does NOT own**: Hotel/Hostel booking truth, Travel Package truth, or Transport Movement truth. It executes the commercial transactions *resulting* from these activities.
- **U-Hotel / U-Hostel**: Hospitality management (PMS-lite).
- **U-Marine / UT**: Transport and logistics movement.
- **PRESTIGE**: Travel demand and channel management.
- **ILUVIA**: Citizen and guest digital access.

## Commerce Workflow (Sovereign Transaction Path)

1. **AEGIS** verifies WHO is acting.
2. **MAC EOS / ORCA** validates WHETHER they are allowed to perform the action.
3. **ExecutionGuard** controls HOW the action is executed.
4. **UPOS** executes WHAT was sold/purchased (the commerce intent).
5. **FCE** calculates money, tax (TGST/GST), and service charges.
6. **SHADOW** seals the event into an immutable audit proof.
7. **APOLLO** ensures resilience for offline island operations.
