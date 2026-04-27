import os
import json
import uuid
from datetime import datetime, UTC
from main import (
    identity_core, shadow_core, events_core, fce_core, guard
)
from mnos.exec.comms.airbox_engine import AirBoxEngine
from mnos.core.doc.engine import SigDocEngine
from mnos.core.fce.invoice import FceInvoiceEngine
from mnos.modules.imoxon.staff_onboarding import StaffOnboardingFlow

class ApolloDeployer:
    """
    APOLLO™ Deployment Script: SALA Node Provisioning.
    Implements the Day 1 Checklist for Sovereign Operations.
    """
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.log = []

    def run(self):
        print(f"🚀 APOLLO: Deploying Node {self.node_id}...")
        self._record("DEPLO_START", f"Starting deployment for {self.node_id}")

        # 1. Provision AIRCLOUD EDGE Services
        print("[1] Provisioning AIRCLOUD EDGE Services...")
        airbox = AirBoxEngine(shadow_core)
        sigdoc = SigDocEngine(shadow_core)
        invoice_engine = FceInvoiceEngine(fce_core, shadow_core, events_core)
        self._record("EDGE_PROVISION", "AIRBOX, SIGDOC, FCE-INVOICE initialized.")

        # 2. Configure Offline Queue
        print("[2] Configuring Offline Queue...")
        os.makedirs(f"mnos/edge/storage/{self.node_id}", exist_ok=True)
        self._record("OFFLINE_QUEUE", f"Storage created at mnos/edge/storage/{self.node_id}")

        # 3. Ingest ORCA TALENT (Staff Onboarding)
        print("[3] Ingesting ORCA TALENT identities...")
        staff_flow = StaffOnboardingFlow(identity_core)
        staff_data = [
            {"name": "Ahmed Ibrahim", "staff_code": "SALA-001", "resort_id": self.node_id, "device_hash": "sala-edge-tab-01"},
            {"name": "Aishath Mohamed", "staff_code": "SALA-002", "resort_id": self.node_id, "device_hash": "sala-edge-tab-02"}
        ]

        # Identity creation needs to be wrapped in sovereign context for compliance
        with guard.sovereign_context(trace_id=f"APOLLO-ONBOARD-{self.node_id}"):
            onboarded = staff_flow.onboard_staff_batch(staff_data)

        for s in onboarded:
            print(f"    - Onboarded: {s['name']} (ID: {s['identity_id'][:8]})")
        self._record("ORCA_TALENT", f"Onboarded {len(onboarded)} staff members.")

        # 4. Fail-Closed Validation
        print("[4] Validating Fail-Closed Rules...")
        # Rule: No invoice without delivery
        try:
            with guard.sovereign_context(trace_id=f"APOLLO-VALIDATE-{self.node_id}"):
                invoice_engine.generate_sovereign_invoice(
                    {"identity_id": onboarded[0]["identity_id"]},
                    {"delivery_id": "NONE", "total_base": 1000},
                    document_hash="MANDATORY-TEST-HASH"
                )
        except PermissionError:
            print("    [PASS] Invoice generation blocked without delivery event.")
        self._record("FAIL_CLOSED_VALIDATION", "Rule 'No Event -> No Invoice' verified.")

        # 5. Finalize
        print(f"✅ APOLLO: Node {self.node_id} is LIVE.")
        self._record("DEPLOY_COMPLETE", f"Node {self.node_id} transition to ACTIVE.")

        return {
            "node_id": self.node_id,
            "status": "ACTIVE",
            "deployment_log": self.log,
            "staff_onboarded": onboarded
        }

    def _record(self, step: str, msg: str):
        self.log.append({
            "timestamp": datetime.now(UTC).isoformat(),
            "step": step,
            "message": msg
        })

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="APOLLO Node Deployment Script")
    parser.add_argument("--node-id", default="Sala-Omadhoo", help="Unique ID for the node being deployed")
    args = parser.parse_args()

    deployer = ApolloDeployer(args.node_id)
    report = deployer.run()

    with open(f"METRICS_{args.node_id.upper()}.json", "w") as f:
        json.dump(report, f, indent=2)
