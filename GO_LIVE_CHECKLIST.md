# Prestige Holidays Core - Go-Live Checklist

## Operational Readiness
- [ ] **Capacity Mapping**: Ensure all room types have correct `capacity` values to prevent over-occupancy.
- [ ] **Tax Configuration**: Verify `mnos/modules/fce/services/tax_service.py` matches current MIRA regulations.
- [ ] **Night Audit**: Schedule end-of-day period close via `perform_night_audit`.

## Integration Hooks
- [ ] **SHADOW Integrity**: Verify that `SHADOW_INTEGRATION_SECRET` is set for immutable evidence signing.
- [ ] **AQUA manifest**: Sync airport arrival times with `TransferRequest.pickup_time`.

## Maintenance Protocol
- [ ] **Blocking Logic**: Train staff that P1/P2 tickets require `CLOSED` status to return rooms to inventory.
- [ ] **QC Workflow**: Ensure `READY_FOR_QC` status is used before `CLOSED` for high-severity issues.
