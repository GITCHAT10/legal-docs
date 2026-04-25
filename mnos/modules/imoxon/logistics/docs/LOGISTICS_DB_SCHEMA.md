# LOGISTICS DATABASE SCHEMA (CITUS DISTRIBUTED)

## Core Entities
- `logistics_shipments`: Master record for inbound goods.
- `logistics_shipment_items`: Line-item detail for shipments.
- `port_clearance_jobs`: Audit trail for port handling and customs.
- `skygodown_receipts`: Warehouse Good Receipt Note (GRN) records.
- `skygodown_lots`: Auditable inventory units grouped by batch.
- `lot_allocations`: Entitlements assigned to resorts/buyers.
- `delivery_manifests`: Load-lists for UT transport vessels.
- `transport_assignments`: Binding between manifest and AEGIS-bound captains.
- `delivery_scan_events`: Immutable log of load/unload actions (Edge supported).
- `delivery_receipts`: Final proof of delivery (POD) with recipient identity.
- `delivery_variances`: Log of detected quantity discrepancies.
- `logistics_audit_events`: Dedicated forensic log for the logistics engine.
