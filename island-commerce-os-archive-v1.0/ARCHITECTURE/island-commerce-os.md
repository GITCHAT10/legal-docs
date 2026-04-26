# 🏝️ BUBBLE Island Commerce OS - Master Architecture Spec

## Overview
The BUBBLE Island Commerce OS is a sovereign economic runtime for the Maldives, integrating guest services, merchant procurement, and financial control.

## Layer Ownership
- **BUBBLE MALL**: Storefront (UI only)
- **BUBBLE WALLET**: Bank (Payment Authority)
- **iMOXON**: Supply Chain (Contracts)
- **Smart Gate**: Risk Controller (Policy)
- **SHADOW LEDGER**: Truth (Immutable Audit)

## Authority Boundaries
Payment authority is cryptographically isolated to the Wallet layer. The Mall never touches guest funds or calculates tax.
