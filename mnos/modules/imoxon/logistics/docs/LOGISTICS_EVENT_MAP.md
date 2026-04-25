# LOGISTICS EVENT TAXONOMY

| Event Type | Logic Point | Business Impact |
| :--- | :--- | :--- |
| `shipment.created` | Engine init | Signal to port authorities of inbound goods. |
| `shipment.dispatched` | Origin scan | Transition to international transit state. |
| `port.clearance_released` | Clearance finalize | Eligible for Skygodown intake. |
| `skygodown.received` | GRN entry | Warehouse custody established. |
| `lot.registered` | Inventory sync | Units available for allocation. |
| `allocation.created` | Demand match | Buyer entitlements locked. |
| `manifest.created` | Transport planning | Load list ready for scan. |
| `transport.assigned` | Captain binding | Legal custody transition to UT. |
| `load.scan.confirmed` | Load scan | Goods physically on vessel. |
| `unload.scan.confirmed` | Unload scan | Goods physically on destination island. |
| `delivery.receipt.confirmed` | Recipient POD | FCE payout release eligible. |
| `delivery.dispute.opened` | Variance > 2% | FCE payout blocked. |
| `fce.release.eligible` | Settlement start | Payment execution to supplier. |
