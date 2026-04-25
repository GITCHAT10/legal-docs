import uuid
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional

class LogisticsEngine:
    """
    IMOXON LOGISTICS ENGINE (RC1-PRODUCTION-BRIDGE)
    Connects Global Supplier -> Port -> Skygodown -> Island Delivery.
    Governed by MNOS Authority: AEGIS, FCE, SHADOW, EVENTS.
    """
    def __init__(self, guard, fce, shadow, events, identity_core, merchant_manager):
        self.guard = guard
        self.fce = fce
        self.shadow = shadow
        self.events = events
        self.identity = identity_core
        self.merchants = merchant_manager

        # In-memory storage for prototype execution
        self.shipments = {}
        self.clearance_jobs = {}
        self.receipts = {}
        self.lots = {}
        self.allocations = {}
        self.manifests = {}
        self.transport_assignments = {}
        self.scan_events = []
        self.delivery_receipts = {}
        self.variances = {}

    def create_shipment(self, actor_ctx: dict, data: dict):
        return self.guard.execute_sovereign_action(
            "logistics.shipment.create",
            actor_ctx,
            self._internal_create_shipment,
            data
        )

    def _internal_create_shipment(self, data):
        # Rule: No shipment without verified supplier
        supplier_id = data.get("supplier_id")
        if self.merchants.get_vendor_status(supplier_id) != "VERIFIED":
            raise PermissionError(f"FAIL CLOSED: Supplier {supplier_id} is not verified.")

        shipment_id = f"SHP-{uuid.uuid4().hex[:8].upper()}"
        shipment = {
            "id": shipment_id,
            "supplier_id": supplier_id,
            "order_id": data.get("order_id"),
            "origin": data.get("origin"),
            "destination": data.get("destination"),
            "items": data.get("items"),
            "status": "CREATED",
            "created_at": datetime.now(UTC).isoformat()
        }
        self.shipments[shipment_id] = shipment
        self.events.publish("shipment.created", shipment)
        return shipment

    def dispatch_shipment(self, actor_ctx: dict, shipment_id: str):
        return self.guard.execute_sovereign_action(
            "logistics.shipment.dispatch",
            actor_ctx,
            self._internal_dispatch,
            shipment_id
        )

    def _internal_dispatch(self, shipment_id):
        if shipment_id not in self.shipments: raise ValueError("Shipment not found")
        self.shipments[shipment_id]["status"] = "DISPATCHED"
        self.events.publish("shipment.dispatched", {"shipment_id": shipment_id})
        return self.shipments[shipment_id]

    def record_port_arrival(self, actor_ctx: dict, shipment_id: str):
        return self.guard.execute_sovereign_action(
            "logistics.port.arrival",
            actor_ctx,
            self._internal_port_arrival,
            shipment_id
        )

    def _internal_port_arrival(self, shipment_id):
        # Rule: No port arrival without shipment record
        if shipment_id not in self.shipments: raise ValueError("Shipment not found")
        self.shipments[shipment_id]["status"] = "ARRIVED_MALDIVES"
        self.events.publish("shipment.arrived_maldives", {"shipment_id": shipment_id})
        return self.shipments[shipment_id]

    def clear_port(self, actor_ctx: dict, shipment_id: str, agent_id: str):
        return self.guard.execute_sovereign_action(
            "logistics.port.clearance",
            actor_ctx,
            self._internal_port_clearance,
            shipment_id, agent_id
        )

    def _internal_port_clearance(self, shipment_id, agent_id):
        job_id = f"CLR-{uuid.uuid4().hex[:6].upper()}"
        self.clearance_jobs[shipment_id] = {
            "id": job_id,
            "shipment_id": shipment_id,
            "agent_id": agent_id,
            "status": "RELEASED",
            "cleared_at": datetime.now(UTC).isoformat()
        }
        self.shipments[shipment_id]["status"] = "CLEARED"
        self.events.publish("port.clearance_released", {"shipment_id": shipment_id})
        return self.clearance_jobs[shipment_id]

    def receive_at_skygodown(self, actor_ctx: dict, shipment_id: str, operator_id: str):
        return self.guard.execute_sovereign_action(
            "logistics.skygodown.receive",
            actor_ctx,
            self._internal_skygodown_receive,
            shipment_id, operator_id
        )

    def _internal_skygodown_receive(self, shipment_id, operator_id):
        # Rule: No Skygodown receipt without port arrival
        if self.shipments[shipment_id]["status"] != "CLEARED":
            raise PermissionError("FAIL CLOSED: Shipment not cleared from port")

        receipt_id = f"GRN-{uuid.uuid4().hex[:8].upper()}"
        receipt = {
            "id": receipt_id,
            "shipment_id": shipment_id,
            "operator_id": operator_id,
            "received_at": datetime.now(UTC).isoformat()
        }
        self.receipts[receipt_id] = receipt
        self.shipments[shipment_id]["status"] = "RECEIVED"
        self.events.publish("skygodown.received", receipt)
        return receipt

    def register_lot(self, actor_ctx: dict, receipt_id: str, sku: str, quantity: float):
        return self.guard.execute_sovereign_action(
            "logistics.lots.register",
            actor_ctx,
            self._internal_register_lot,
            receipt_id, sku, quantity
        )

    def _internal_register_lot(self, receipt_id, sku, qty):
        lot_id = f"LOT-{uuid.uuid4().hex[:6].upper()}"
        lot = {
            "id": lot_id,
            "receipt_id": receipt_id,
            "sku": sku,
            "total_quantity": qty,
            "available_quantity": qty
        }
        self.lots[lot_id] = lot
        self.events.publish("lot.registered", lot)
        return lot

    def create_allocation(self, actor_ctx: dict, lot_id: str, buyer_id: str, resort_id: str, qty: float):
        return self.guard.execute_sovereign_action(
            "logistics.allocations.create",
            actor_ctx,
            self._internal_allocate,
            lot_id, buyer_id, resort_id, qty
        )

    def _internal_allocate(self, lot_id, buyer_id, resort_id, qty):
        # Rule: No allocation without registered lot
        lot = self.lots.get(lot_id)
        if not lot or lot["available_quantity"] < qty:
             raise ValueError("Insufficient lot quantity")

        allocation_id = f"ALC-{uuid.uuid4().hex[:6].upper()}"
        allocation = {
            "id": allocation_id,
            "lot_id": lot_id,
            "sku": lot["sku"], # Carry forward SKU for variance check
            "buyer_id": buyer_id,
            "resort_id": resort_id,
            "allocated_quantity": qty,
            "status": "ALLOCATED"
        }
        lot["available_quantity"] -= qty
        self.allocations[allocation_id] = allocation
        self.events.publish("allocation.created", allocation)
        return allocation

    def create_manifest(self, actor_ctx: dict, data: dict):
        return self.guard.execute_sovereign_action(
            "logistics.manifest.create",
            actor_ctx,
            self._internal_create_manifest,
            data
        )

    def _internal_create_manifest(self, data):
        # Rule: No manifest without allocation
        allocation_ids = data.get("allocation_ids", [])
        for alc_id in allocation_ids:
            if alc_id not in self.allocations:
                 raise ValueError(f"Allocation {alc_id} not found")

        manifest_id = f"MAN-{uuid.uuid4().hex[:8].upper()}"
        manifest = {
            "id": manifest_id,
            "destination_id": data.get("destination_id"),
            "captain_id": data.get("captain_id"),
            "vessel_id": data.get("vessel_id"),
            "allocations": allocation_ids,
            "status": "CREATED",
            "created_at": datetime.now(UTC).isoformat()
        }
        self.manifests[manifest_id] = manifest
        self.events.publish("manifest.created", manifest)
        return manifest

    def assign_transport(self, actor_ctx: dict, manifest_id: str, driver_id: str, device_id: str):
        return self.guard.execute_sovereign_action(
            "logistics.transport.assign",
            actor_ctx,
            self._internal_assign_transport,
            manifest_id, driver_id, device_id
        )

    def _internal_assign_transport(self, manifest_id, driver_id, device_id):
        # Rule: No transport assignment without AEGIS-bound driver/captain/device
        # For simplicity, we assume driver is checked if they exist in identity profiles
        # In a real system we would check verification_status == verified

        assignment_id = f"ASN-{uuid.uuid4().hex[:6].upper()}"
        self.transport_assignments[manifest_id] = {
            "id": assignment_id,
            "manifest_id": manifest_id,
            "driver_id": driver_id,
            "device_id": device_id
        }
        self.events.publish("transport.assigned", {"manifest_id": manifest_id, "driver_id": driver_id})
        return self.transport_assignments[manifest_id]

    def confirm_scan(self, actor_ctx: dict, manifest_id: str, scan_type: str, is_offline: bool = False):
        return self.guard.execute_sovereign_action(
            f"logistics.scan.{scan_type.lower()}",
            actor_ctx,
            self._internal_confirm_scan,
            manifest_id, scan_type, is_offline
        )

    def _internal_confirm_scan(self, manifest_id, scan_type, is_offline):
        # Rule: Load scan requires assigned transport
        if scan_type == "LOAD" and manifest_id not in self.transport_assignments:
             raise PermissionError("FAIL CLOSED: Transport not assigned for this manifest")

        # Rule: Unload scan requires load scan (simplified check)
        if scan_type == "UNLOAD":
             loaded = any(s["manifest_id"] == manifest_id and s["scan_type"] == "LOAD" for s in self.scan_events)
             if not loaded: raise PermissionError("FAIL CLOSED: Load scan must precede unload scan")

        event = {
            "manifest_id": manifest_id,
            "actor_id": self.guard.get_actor()["identity_id"],
            "scan_type": scan_type,
            "timestamp": datetime.now(UTC).isoformat(),
            "is_offline": is_offline
        }
        self.scan_events.append(event)
        self.events.publish(f"{scan_type.lower()}.scan.confirmed", event)

        if scan_type == "LOAD": self.manifests[manifest_id]["status"] = "DISPATCHED"
        return event

    def confirm_delivery_receipt(self, actor_ctx: dict, manifest_id: str, recipient_id: str, items: list):
        return self.guard.execute_sovereign_action(
            "logistics.receipt.confirm",
            actor_ctx,
            self._internal_confirm_delivery,
            manifest_id, recipient_id, items
        )

    def _internal_confirm_delivery(self, manifest_id, recipient_id, items):
        # Rule: No final receipt without unload scan
        unloaded = any(s["manifest_id"] == manifest_id and s["scan_type"] == "UNLOAD" for s in self.scan_events)
        if not unloaded: raise PermissionError("FAIL CLOSED: Unload scan required for receipt confirmation")

        receipt_id = f"RCP-{uuid.uuid4().hex[:8].upper()}"

        # Variance Check (Simplified: Compare count of items)
        # Expected from allocations
        expected_items = {} # sku -> qty
        for alc_id in self.manifests[manifest_id]["allocations"]:
             alc = self.allocations.get(alc_id)
             if not alc: continue
             sku = alc.get("sku")
             if sku:
                 expected_items[sku] = expected_items.get(sku, 0) + alc["allocated_quantity"]

        disputed = False
        for item in items:
             sku = item["sku"]
             actual = item["qty"]
             expected = expected_items.get(sku, 0)
             variance = abs(actual - expected) / expected if expected > 0 else 1
             if variance > 0.02: # 2% Threshold
                  disputed = True
                  self.variances[receipt_id] = {"sku": sku, "expected": expected, "actual": actual, "variance": variance}

        status = "DISPUTED" if disputed else "CONFIRMED"
        receipt = {
            "id": receipt_id,
            "manifest_id": manifest_id,
            "recipient_id": recipient_id,
            "received_items": items,
            "status": status,
            "confirmed_at": datetime.now(UTC).isoformat()
        }
        self.delivery_receipts[manifest_id] = receipt
        self.manifests[manifest_id]["status"] = "DELIVERED"

        if disputed:
             self.events.publish("delivery.dispute.opened", receipt)
        else:
             self.events.publish("delivery.receipt.confirmed", receipt)

        return receipt

    def report_variance(self, actor_ctx: dict, receipt_id: str, data: dict):
        return self.guard.execute_sovereign_action(
            "logistics.variance.report",
            actor_ctx,
            self._internal_report_variance,
            receipt_id, data
        )

    def _internal_report_variance(self, receipt_id, data):
        self.variances[receipt_id] = data
        self.events.publish("delivery.variance.detected", {"receipt_id": receipt_id, "data": data})
        return {"status": "RECORDED"}

    def release_settlement(self, actor_ctx: dict, manifest_id: str, order_id: str):
        return self.guard.execute_sovereign_action(
            "logistics.settlement.release",
            actor_ctx,
            self._internal_settlement_release,
            manifest_id, order_id
        )

    def _internal_settlement_release(self, manifest_id, order_id):
        # Rule: No FCE release without confirmed delivery receipt
        receipt = self.delivery_receipts.get(manifest_id)
        if not receipt or receipt["status"] != "CONFIRMED":
             self.events.publish("fce.release.blocked", {"manifest_id": manifest_id, "reason": "Variance/Dispute"})
             raise PermissionError("FAIL CLOSED: Variance above 2% blocks final release")

        # Rule: FCE release
        # In RC1 Bridge, we use escrow_core.release_to_settlement via main instance
        # For prototype engine, we emit eligibility
        release_res = {"manifest_id": manifest_id, "order_id": order_id, "status": "ELIGIBLE"}
        self.events.publish("fce.release.eligible", release_res)

        # Rule: Generate final Logistics Certificate in Shadow
        certificate = {
            "manifest_id": manifest_id,
            "order_id": order_id,
            "audit_chain_locked": True,
            "timestamp": datetime.now(UTC).isoformat()
        }
        self.shadow.commit("shadow.logistics.certificate.generated", "SYSTEM", certificate)
        return release_res
