# IMOXON FLOW MATRIX

| Route | Guard Action | Finance Rule | Ledger Entry | Shadow Proof |
|-------|--------------|--------------|--------------|--------------|
| /commerce/orders/create | imoxon.order.create | 10% SC + 17% TGST | Transaction Record | order.created |
| /commerce/vendors/approve | imoxon.vendor.approve | N/A | Vendor Activation | vendor.approved |
| /commerce/milestones/verify | imoxon.milestone.verify | N/A | Proof Registry | milestone.verified |
| /commerce/payouts/release | imoxon.payment.release | Milestone % (10-40%) | Payout Release | payment.released |
| /commerce/shipment/dispatch | imoxon.shipment.dispatch | N/A | Manifest Creation | shipment.dispatched |
| /commerce/shipment/receive | imoxon.shipment.receive | N/A | Receipt Audit | shipment.received |
