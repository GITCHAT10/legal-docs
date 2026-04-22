from typing import Dict, Any
from mnos.core.ai.parser import BuildingRequest
from mnos.modules.compliance.checker import check_maldives_compliance
from mnos.modules.layout.generator import generate_layout
from mnos.modules.finance.boq import calculate_boq_and_cost
import hashlib
import json

class ArcoManager:
    """
    ARCOs Architecture: Sovereign Construction Orchestration.
    Enforces MNOS Doctrine: Design -> ELEONE -> AEGIS -> FCE -> SHADOW -> EVENTS.
    """
    def __init__(self, event_bus, shadow_logger):
        self.bus = event_bus
        self.shadow = shadow_logger

    def execute_build_pipeline(self, request: BuildingRequest) -> Dict[str, Any]:
        trace_id = hashlib.sha256(json.dumps(request.model_dump()).encode()).hexdigest()[:8]

        # 1. AEGIS Compliance (Validation)
        compliance = check_maldives_compliance(request)
        if not compliance["is_compliant"]:
            self.shadow.log("BUILD_REJECTED_AEGIS", {"trace_id": trace_id, "violations": compliance["violations"]})
            return {"status": "REJECTED", "reason": "AEGIS Violation", "errors": compliance["violations"]}

        # 2. SIE Geometry (Design)
        layout = generate_layout(request, compliance)
        if "error" in layout:
            self.shadow.log("BUILD_REJECTED_SIE", {"trace_id": trace_id, "error": layout["error"]})
            return {"status": "REJECTED", "reason": "Geometric Failure", "error": layout["error"]}

        # 3. FCE Ledger (Financial Authority)
        boq = calculate_boq_and_cost(layout, event_bus=self.bus)

        # 4. SHADOW Immutable Commit
        audit_entry = {
            "trace_id": trace_id,
            "request": request.model_dump(),
            "ledger": boq["fce_ledger"],
            "status": "APPROVED"
        }
        self.shadow.log("CONSTRUCTION_LOCK_COMMITTED", audit_entry)

        # 5. MNOS EVENTS Emission
        self.bus.emit("ARCOS_BUILD_AUTHORIZED", {
            "trace_id": trace_id,
            "plot": request.plot.model_dump(),
            "budget": boq["fce_ledger"]["total_commitment"]
        })

        return {
            "status": "SUCCESS",
            "trace_id": trace_id,
            "layout": layout,
            "boq": boq,
            "compliance": compliance
        }
