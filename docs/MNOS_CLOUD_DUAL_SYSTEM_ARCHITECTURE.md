# MNOS Cloud Dual System Architecture

## Overview
This document describes the logical isolation and secure synchronization between **NEXUS-SKYI HMS** and **iMOXON Marketplace** within the MNOS Sovereign Cloud.

## Logical Isolation
- **HMS Tenant**: Guest data, financial folios, internal inventory.
- **iMOXON Tenant**: Vendor bids, global procurement, logistics.
- **Boundary**: No direct database or file access between tenants.

## Communication: The API Airlock
All cross-tenant interactions must pass through the **API Airlock** which enforces:
- AEGIS Node verification
- Ed25519 Request Signing
- SHADOW Trace Logging
- 60s Timestamp Drift Check
- Nonce Anti-Replay

## Security Stack
- **Network**: Private same-cloud bridge, ORBAN/WireGuard for admin.
- **Audit**: Every cross-tenant request is committed to AIGShadow.
- **Execution**: ExecutionGuard prevents bypass of isolation rules.
