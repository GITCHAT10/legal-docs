import logging
import uuid
import hashlib
from typing import Dict, Optional, Any, List
from decimal import Decimal

from mnos.modules.admiralda.schemas import (
    CommandExecutionResult, ParsedVoiceCommand, VerifiedActor,
    PolicyDecision, FcePrecheckResult, ModuleExecutionResult, ShadowCommitResult
)
# Assuming these services exist based on common MNOS patterns
from mnos.modules.shadow import service as shadow_service
from mnos.core.events.dispatcher import event_dispatcher

class AmbiguousCommandError(Exception):
    pass

class AdmiraldaService:
    def __init__(self, db_session=None):
        self.db = db_session
        # In a real system, these would be injected or looked up via a service registry
        self.id_factory = type('IdFactory', (), {'new': lambda self: str(uuid.uuid4())})()

    async def execute_voice_command(
        self,
        transcript: str,
        channel: str,
        session_id: str,
        caller_id: str | None = None,
        metadata: dict | None = None,
    ) -> CommandExecutionResult:
        command_id = self.id_factory.new()

        try:
            # 1. Parse
            parsed = await self.parse_voice_command(transcript)

            # 2. Verify actor with AEGIS
            actor = await self.verify_actor_with_aegis(
                caller_id=caller_id,
                session_id=session_id,
                metadata=metadata,
            )

            # 3. Authorize command
            policy = await self.authorize_command(actor, parsed)
            if not policy.allowed:
                return CommandExecutionResult(
                    status="rejected",
                    command_id=command_id,
                    actor_id=actor.actor_id,
                    session_id=session_id,
                    transcript=transcript,
                    normalized_text=parsed.normalized_text,
                    intent=parsed.intent,
                    target_module=parsed.target_module,
                    policy_decision=policy.decision,
                    reason_code=policy.reason_code,
                    human_message="You are not authorized for that command.",
                )

            # 4. Run FCE precheck if needed
            fce_result = None
            if parsed.requires_fce:
                fce_result = await self.run_fce_precheck_if_needed(actor, parsed)
                if not fce_result.passed:
                    return CommandExecutionResult(
                        status="rejected",
                        command_id=command_id,
                        actor_id=actor.actor_id,
                        session_id=session_id,
                        transcript=transcript,
                        normalized_text=parsed.normalized_text,
                        intent=parsed.intent,
                        target_module=parsed.target_module,
                        policy_decision="allow",
                        reason_code="FCE_PRECHECK_FAILED",
                        requires_fce=True,
                        fce_check_passed=False,
                        human_message="That request did not pass financial control checks.",
                    )

            # 5. Dispatch to target module
            module_result = await self.dispatch_to_module(actor, parsed, fce_result)
            if not module_result.success:
                return CommandExecutionResult(
                    status="failed",
                    command_id=command_id,
                    actor_id=actor.actor_id,
                    session_id=session_id,
                    transcript=transcript,
                    normalized_text=parsed.normalized_text,
                    intent=parsed.intent,
                    target_module=parsed.target_module,
                    policy_decision="allow",
                    requires_fce=parsed.requires_fce,
                    fce_check_passed=(fce_result.passed if fce_result else None),
                    human_message=module_result.human_message,
                )

            # 6. Commit to SHADOW
            shadow = await self.commit_shadow_record(actor, parsed, module_result, fce_result)
            if not shadow.success:
                # Sovereignty rule: If SHADOW fails, treat the entire command as failed.
                return CommandExecutionResult(
                    status="failed",
                    command_id=command_id,
                    session_id=session_id,
                    transcript=transcript,
                    normalized_text=parsed.normalized_text,
                    policy_decision="allow",
                    reason_code="SHADOW_COMMIT_FAILURE",
                    human_message="The command could not be completed safely (Audit Failure).",
                )

            # 7. Emit events
            events = await self.emit_events(shadow, module_result)

            return CommandExecutionResult(
                status="accepted",
                command_id=command_id,
                actor_id=actor.actor_id,
                session_id=session_id,
                transcript=transcript,
                normalized_text=parsed.normalized_text,
                intent=parsed.intent,
                target_module=module_result.target_module,
                policy_decision="allow",
                requires_fce=parsed.requires_fce,
                fce_check_passed=(fce_result.passed if fce_result else None),
                shadow_commit_id=shadow.commit_id,
                events_emitted=events,
                execution_payload=module_result.payload,
                human_message=module_result.human_message,
            )

        except AmbiguousCommandError:
            return CommandExecutionResult(
                status="rejected",
                command_id=command_id,
                session_id=session_id,
                transcript=transcript,
                normalized_text=transcript.strip(),
                policy_decision="deny",
                reason_code="AMBIGUOUS_COMMAND",
                human_message="I understood the request only partially, so I did not execute it.",
            )
        except Exception as e:
            logging.exception(f"Unhandled execution failure for command {command_id}")
            return CommandExecutionResult(
                status="failed",
                command_id=command_id,
                session_id=session_id,
                transcript=transcript,
                normalized_text=transcript.strip(),
                policy_decision="deny",
                reason_code="UNHANDLED_EXECUTION_FAILURE",
                human_message="The command could not be completed safely.",
            )

    async def parse_voice_command(self, transcript: str) -> ParsedVoiceCommand:
        normalized = transcript.lower().strip()
        if not normalized:
            raise AmbiguousCommandError("Empty transcript")

        # Deterministic NLU Mapping (v1)
        if any(word in normalized for word in ["reservation", "booking", "look up"]):
            return ParsedVoiceCommand(
                normalized_text=normalized,
                intent="reservation.lookup",
                confidence=0.98,
                target_module="INN",
                requires_fce=False
            )
        elif any(word in normalized for word in ["folio", "balance", "bill"]):
            return ParsedVoiceCommand(
                normalized_text=normalized,
                intent="folio.balance_inquiry",
                confidence=0.99,
                target_module="INN",
                requires_fce=False
            )
        elif any(word in normalized for word in ["payment link", "generate link", "pay"]):
            return ParsedVoiceCommand(
                normalized_text=normalized,
                intent="payment.link_generate",
                confidence=0.96,
                target_module="FCE",
                requires_fce=True,
                risk_level="medium"
            )
        elif any(word in normalized for word in ["room status", "cleaned"]):
            return ParsedVoiceCommand(
                normalized_text=normalized,
                intent="room.status_inquiry",
                confidence=0.95,
                target_module="INN",
                requires_fce=False
            )
        elif any(word in normalized for word in ["fix", "broken", "maintenance"]):
            return ParsedVoiceCommand(
                normalized_text=normalized,
                intent="maintenance.ticket_create",
                confidence=0.94,
                target_module="MAINTAIN",
                requires_fce=False
            )
        elif any(word in normalized for word in ["boat", "transfer", "speedboat"]):
            return ParsedVoiceCommand(
                normalized_text=normalized,
                intent="transfer.status_inquiry",
                confidence=0.97,
                target_module="AQUA",
                requires_fce=False
            )
        elif any(word in normalized for word in ["help", "operator", "human", "escalate"]):
            return ParsedVoiceCommand(
                normalized_text=normalized,
                intent="human.escalation",
                confidence=1.0,
                target_module="ADMIRALDA",
                requires_fce=False
            )

        # Fallback for ambiguous commands
        if len(normalized.split()) < 2:
             raise AmbiguousCommandError("Command too short/ambiguous")

        # If no specific mapping but seems like a command, we might still reject for confidence
        raise AmbiguousCommandError("Intent not recognized")

    async def verify_actor_with_aegis(
        self,
        caller_id: str | None,
        session_id: str,
        metadata: dict | None = None,
    ) -> VerifiedActor:
        # v1 Mock: In production, call AEGIS service
        if not session_id or session_id == "EXPIRED":
            raise Exception("AEGIS: Invalid or expired session")

        # Simulate voice mismatch
        if metadata and metadata.get("voice_match_score", 1.0) < 0.96:
            raise Exception("AEGIS: Voiceprint mismatch threshold not met")

        return VerifiedActor(
            actor_id="ACTOR-007",
            tenant_id="TENANT-MALDIVES-OG",
            property_id="PROP-SALA",
            roles=["agent", "guest_service"],
            auth_strength="standard",
            verification_confidence=0.99
        )

    async def authorize_command(
        self,
        actor: VerifiedActor,
        cmd: ParsedVoiceCommand,
    ) -> PolicyDecision:
        # Check role-based access
        if cmd.risk_level == "high" and "supervisor" not in actor.roles:
            return PolicyDecision(allowed=False, decision="deny", reason_code="INSUFFICIENT_PERMISSIONS")

        # Tenant Isolation
        if actor.tenant_id != "TENANT-MALDIVES-OG":
             return PolicyDecision(allowed=False, decision="deny", reason_code="TENANT_MISMATCH")

        return PolicyDecision(allowed=True, decision="allow")

    async def run_fce_precheck_if_needed(
        self,
        actor: VerifiedActor,
        cmd: ParsedVoiceCommand,
    ) -> FcePrecheckResult | None:
        # Economic effect check
        if cmd.intent == "payment.link_generate":
            # Check if actor can generate payments
            if "agent" not in actor.roles:
                return FcePrecheckResult(passed=False, reason="Actor lacks financial role")
            return FcePrecheckResult(passed=True, transaction_id=f"FCE-PRE-{uuid.uuid4().hex[:8]}")

        return FcePrecheckResult(passed=True)

    async def dispatch_to_module(
        self,
        actor: VerifiedActor,
        cmd: ParsedVoiceCommand,
        fce_result: FcePrecheckResult | None = None,
    ) -> ModuleExecutionResult:
        # Orchestration to MNOS modules via their service interfaces
        if cmd.target_module == "INN":
            return ModuleExecutionResult(
                success=True,
                target_module="INN",
                action=cmd.intent,
                payload={"info": "Data from INN service"},
                human_message=f"I have retrieved the {cmd.intent.split('.')[-1]} from INN."
            )
        elif cmd.target_module == "FCE":
            return ModuleExecutionResult(
                success=True,
                target_module="FCE",
                action=cmd.intent,
                payload={"payment_link": "https://pay.mnos.mv/token/abc-123"},
                human_message="The payment link has been generated."
            )
        elif cmd.target_module == "AQUA":
            return ModuleExecutionResult(
                success=True,
                target_module="AQUA",
                action=cmd.intent,
                human_message="Transfer status is: On Time."
            )
        elif cmd.target_module == "MAINTAIN":
             return ModuleExecutionResult(
                success=True,
                target_module="MAINTAIN",
                action=cmd.intent,
                record_id=f"TICKET-{uuid.uuid4().hex[:4].upper()}",
                human_message="Maintenance ticket created successfully."
            )

        return ModuleExecutionResult(
            success=False,
            target_module=cmd.target_module or "UNKNOWN",
            action=cmd.intent,
            human_message="Target module not integrated or unreachable."
        )

    async def commit_shadow_record(
        self,
        actor: VerifiedActor,
        cmd: ParsedVoiceCommand,
        module_result: ModuleExecutionResult,
        fce_result: FcePrecheckResult | None = None,
    ) -> ShadowCommitResult:
        # Immutable Evidence Chain
        evidence_payload = {
            "actor_id": actor.actor_id,
            "transcript_hash": hashlib.sha384(cmd.normalized_text.encode()).hexdigest(),
            "intent": cmd.intent,
            "module_result": module_result.success,
            "fce_tx": fce_result.transaction_id if fce_result else None
        }

        try:
            # In production, this writes to the SHADOW module's append-only ledger
            if self.db:
                 shadow_service.commit_evidence(self.db, str(uuid.uuid4()), evidence_payload)

            return ShadowCommitResult(success=True, commit_id=f"SHADOW-{uuid.uuid4().hex[:8]}")
        except Exception as e:
            logging.error(f"SHADOW commit failed: {e}")
            return ShadowCommitResult(success=False)

    async def emit_events(
        self,
        shadow: ShadowCommitResult,
        module_result: ModuleExecutionResult,
    ) -> List[str]:
        events = ["ADMIRALDA_COMMAND_EXECUTED"]

        main_event = f"ADMIRALDA_{module_result.target_module}_{module_result.action.upper().replace('.', '_')}"
        events.append(main_event)

        # Dispatch via MNOS event bus
        event_dispatcher.dispatch(main_event, {
            "shadow_id": shadow.commit_id,
            "payload": module_result.payload
        })

        return events
