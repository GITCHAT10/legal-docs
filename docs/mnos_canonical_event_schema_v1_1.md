# MNOS Canonical Event Schema v1.1

## Overview
Standardized schema for all events within the MNOS ecosystem.

## Required Fields
- `event_id`: UUID
- `event_type`: Regex `^[A-Z][A-Z0-9_]*\.[A-Z][A-Z0-9_]*\.[A-Z][A-Z0-9_]*$`
- `timestamp`: ISO8601 DateTime
- `source`:
  - `system`: Enum (CORE, UPOS, MAC_EOS, etc.)
- `actor`:
  - `id`: String
  - `role`: String
- `context`:
  - `tenant`: (brand, tin, jurisdiction)
- `payload`: Object
- `proof`: Proof of validation/settlement
- `metadata`:
  - `schema_version`: "1.1" (Locked)

## Namespace Policy
Source system must match logical event prefix:
- `QRD_MIG_SHIELD` -> `QRD.*`
- `ESG_TERRAFORM` -> `ESG.*`
- ... (see `namespace_mapping.py`)
