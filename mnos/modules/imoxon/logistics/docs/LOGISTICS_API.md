# LOGISTICS API SPECIFICATION (v1)

## Base Path: `/api/v1/logistics`

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/shipment/create` | POST | Create a new inbound shipment from a verified supplier. |
| `/shipment/{id}/dispatch` | POST | Mark shipment as dispatched from origin. |
| `/port/arrival` | POST | Record arrival at Maldives port. |
| `/port/{id}/clearance` | POST | Finalize port/customs clearance. |
| `/skygodown/receive` | POST | Warehouse intake and status update to RECEIVED. |
| `/lots/register` | POST | Register warehouse items as auditable Lots. |
| `/allocations/create` | POST | Allocate lot quantities to specific buyers/resorts. |
| `/manifest/create` | POST | Group allocations into a delivery manifest. |
| `/transport/assign` | POST | Assign AEGIS-bound transport (captain/vessel). |
| `/scan/load` | POST | Confirm goods loaded onto vessel. |
| `/scan/unload` | POST | Confirm goods unloaded at destination island. |
| `/receipt/confirm` | POST | Final recipient confirmation with variance check. |
| `/settlement/release` | POST | Release held funds to supplier (FCE release). |
| `/track/{id}` | GET | Retrieve full lifecycle state of a shipment. |
