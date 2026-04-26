# iMOXON Consolidated Architecture

## Component Overview

### 1. Super App Layer (BUBBLE OS)
- **iMOXON Interface**: Marketplace and Merchant dashboards.
- **Bubble SDK**: Bridge for local mini-apps.
- **ChatIntent**: Natural language to transaction mapping.

### 2. Governance Layer (MNOS/MAC EOS)
- **AEGIS**: Identity authority (DID, KYB/KYC).
- **FCE**: Financial authority (Tax, Escrow, Clearing).
- **SHADOW**: Forensic truth (Immutable ledger).
- **EVENTS**: Orchestration (System-wide bus).

### 3. Execution Layer (iMOXON Core)
- **BPE**: POS and Inventory.
- **Logistics**: Clearance and transport.
- **Procurement**: Supply chain and B2B.

## Transaction Security
Every mutating action must pass through the `ExecutionGuard`.
Direct writes to modules are prohibited by `_sovereign_context` enforcement.

## Failover (Protocol 0200)
Supports island-local operation during connectivity loss.
Transaction WAL and post-connectivity reconciliation.
