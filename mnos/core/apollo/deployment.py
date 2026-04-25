from typing import Dict, Any, List
from mnos.modules.aig_shadow.service import aig_shadow
from mnos.shared.guard.service import guard

class ApolloDeployment:
    """
    Apollo Control Plane: Deployment Governance.
    Enforces LAB → PILOT → PROD → ELITE progression.
    Requires attestation before state transition.
    """
    TIERS = ["LAB", "PILOT", "PROD", "ELITE"]

    def __init__(self):
        self.current_state = "LAB"
        self.health_status = "PASS"

    def deploy(self, artifact_hash: str, target_tier: str, session_context: Dict[str, Any], attestation: Dict[str, Any], connection_context: Dict[str, Any] = None):
        """
        Executes a guarded deployment.
        MIG HARDENING: No deployment without attestation and SHADOW proof.
        """
        def deploy_logic(p):
            # Verify progression
            current_idx = self.TIERS.index(self.current_state)
            target_idx = self.TIERS.index(p["target_tier"])

            if target_idx > current_idx + 1:
                raise RuntimeError(f"APOLLO: Illegal tier jump from {self.current_state} to {p['target_tier']}")

            # Verify Attestation
            if not p["attestation"].get("artifact_hash_match"):
                 raise RuntimeError("APOLLO: Artifact hash mismatch in attestation.")

            if not p["attestation"].get("guard_proof_report"):
                 raise RuntimeError("APOLLO: Missing guard proof report in attestation.")

            # Transition state
            self.current_state = p["target_tier"]
            return {"status": "DEPLOYED", "tier": self.current_state, "artifact": p["artifact_hash"]}

        return guard.execute_sovereign_action(
            action_type="apollo.deploy",
            payload={"artifact_hash": artifact_hash, "target_tier": target_tier, "attestation": attestation},
            session_context=session_context,
            execution_logic=deploy_logic,
            connection_context=connection_context,
            tenant="MIG-GENESIS",
            objective_code="H2" # Deployment Objective
        )

apollo_deploy = ApolloDeployment()
