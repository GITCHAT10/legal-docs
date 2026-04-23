# Prestige Holidays Core - Module Map

The system follows the canonical **MNOS architecture**, separating core governance from commercial interfaces and execution modules.

## Core Governance (`/mnos/core`)
- **API Gateway**: Mandatory entry point with signature/idempotency enforcement.
- **Security**: RBAC, JWT, and HMAC validation.
- **DB**: Centralized session management and base classes.
- **Events**: Redis/Mock-based event bus for cross-module communication.

## Commercial Interface (`/mnos/interfaces/prestige`)
- **Guests**: Profile management and duplicate detection.
- **Main**: Application bootstrap and route orchestration.

## Execution Modules (`/mnos/modules`)
- **INN**:
  - **Reservations**: Booking logic, stay tracking, and room status management.
  - **Staging (Whale Intake)**: Bulk rooming list ingestion with strict validation.
- **FCE (Financial Control Engine)**:
  - Authoritative ledger, Maldives tax logic (10% SC, 17% TGST), and Folio management.
- **AQUA (Transfers)**:
  - Movement layer: vehicle assignment, manifests, and route tracking.
- **SHADOW**:
  - Immutable audit ledger. All state-changing operations across modules commit evidence here.
- **MAINTAIN**:
  - Maintenance/OOO Engine with room blocking, SLA tracking, and QC-gated room release.
