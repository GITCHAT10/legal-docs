# IMOXON CONSOLIDATED ARCHITECTURE

## Overview
iMOXON is the unified Maldives B2B + B2C sourcing, procurement, marketplace, finance, and logistics operating layer. It consolidates multiple disparate commerce systems into a single, sovereign-hardened grid.

## Core Positioning
iMOXON = Maldives Commerce + Sourcing Grid

## Final Module Structure
```text
mnos/modules/imoxon/
  core/           # Unified execution hub
  catalog/        # Normalized product data
  suppliers/      # Sourcing grid nodes
  marketplace/    # B2B/B2C logic
  procurement/    # Bulk RFP/PO engine
  pricing/        # Landed cost & tax core
  orders/         # Transaction manager
  warehouse/      # Inventory & stock
  logistics/      # Dispatch & routing
  finance/        # Settlement & payout
  trust/          # KYC & risk scoring
  audit/          # Shadow traceability
  integrations/   # External supplier bridges
```

## Architecture Rule
All commerce actions MUST flow through:
**AEGIS → iMOXON CORE → FCE → EVENTS → SHADOW**

### Enforcements
- No direct database writes.
- No product listing without admin approval.
- No order settlement without FCE validation.
- Every state change is audited via the SHADOW hash chain.
- Landed cost calculation includes 15% shipping/customs + 10% markup + 17% TGST (B2B).
