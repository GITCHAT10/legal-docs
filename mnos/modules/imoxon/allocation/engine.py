import uuid
from typing import List, Dict

class AllocationEngine:
    """
    iMOXON Allocation Engine: Enforces fair distribution and SKU splitting.
    Priority: Medical > Gov > Resort
    """
    def __init__(self, shadow):
        self.shadow = shadow
        self.batches = {} # batch_id -> {total, allocated, remaining}

    def process_intake(self, actor_id: str, sku: str, total_qty: int):
        from mnos.shared.execution_guard import ExecutionGuard
        batch_id = f"BAT-{uuid.uuid4().hex[:6].upper()}"
        self.batches[batch_id] = {
            "sku": sku,
            "total": total_qty,
            "allocated": 0,
            "remaining": total_qty,
            "allocations": []
        }
        actor = {"identity_id": actor_id, "device_id": "IMOXON-INTAKE", "role": "admin"}
        with ExecutionGuard.authorized_context(actor):
            self.shadow.commit("allocation.intake", actor_id, {"batch_id": batch_id, "sku": sku, "qty": total_qty}, trace_id=f"TR-ALLOC-INTAKE-{batch_id}")
        return batch_id

    def allocate(self, actor_id: str, batch_id: str, requests: List[Dict]):
        """
        requests: [{entity_id, type, requested_qty}]
        Sorting by priority rules.
        """
        if batch_id not in self.batches:
            raise ValueError("Batch not found")

        batch = self.batches[batch_id]
        # Sort: Medical (1), Gov (2), Resort (3)
        priority_map = {"medical": 1, "gov": 2, "resort": 3}
        sorted_reqs = sorted(requests, key=lambda x: priority_map.get(x["type"], 99))

        for req in sorted_reqs:
            if batch["remaining"] <= 0:
                break

            alloc_qty = min(req["requested_qty"], batch["remaining"])
            batch["allocated"] += alloc_qty
            batch["remaining"] -= alloc_qty

            alloc_record = {
                "entity_id": req["entity_id"],
                "type": req["type"],
                "qty": alloc_qty
            }
            batch["allocations"].append(alloc_record)

        from mnos.shared.execution_guard import ExecutionGuard
        actor = {"identity_id": actor_id, "device_id": "IMOXON-ALLOC", "role": "admin"}
        with ExecutionGuard.authorized_context(actor):
            self.shadow.commit("allocation.locked", actor_id, {"batch_id": batch_id, "allocations": batch["allocations"]}, trace_id=f"TR-ALLOC-LOCK-{batch_id}")
        return batch["allocations"]
