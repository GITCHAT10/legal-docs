class ApolloOrchestrator:
    """
    Sovereign Orchestrator: Links logistics milestones to financial releases.
    """
    def __init__(self, guard, shadow, events):
        self.guard = guard
        self.shadow = shadow
        self.events = events
        self.milestone_proofs = {}

    def record_milestone_proof(self, actor_ctx: dict, proof_data: dict):
        return self.guard.execute_sovereign_action(
            "imoxon.milestone.verify",
            actor_ctx,
            self._internal_record_proof,
            proof_data
        )

    def _internal_record_proof(self, proof_data: dict):
        milestone = proof_data.get("milestone")
        ref_id = proof_data.get("ref_id")
        key = f"{ref_id}:{milestone}"

        self.milestone_proofs[key] = {
            "verified": True,
            "timestamp": proof_data.get("timestamp"),
            "actor": self.guard.get_actor().get("identity_id")
        }
        self.events.publish("milestone.verified", {"key": key, "status": "SEALED"})
        return True

    def trigger_milestone_payout(self, actor_ctx: dict, fce, milestone: str, data: dict):
        return self.guard.execute_sovereign_action(
            "imoxon.payment.release",
            actor_ctx,
            self._internal_trigger_payout,
            fce, milestone, data
        )

    def _internal_trigger_payout(self, fce, milestone: str, data: dict):
        # 1. HARD BLOCK: Verify Milestone Proof in SHADOW/State
        ref_id = data.get("ref_id")
        key = f"{ref_id}:{milestone}"
        if not self.milestone_proofs.get(key, {}).get("verified"):
            raise PermissionError(f"FAIL CLOSED: No verified SHADOW proof for milestone {milestone}")

        # 2. Authorized FCE Release
        release = fce.calculate_milestone_release(milestone, data)
        self.events.publish("payment.released", release)
        return release
