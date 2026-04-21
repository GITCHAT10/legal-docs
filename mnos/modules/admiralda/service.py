import logging
import uuid
import hashlib
from typing import Dict, Optional, Any, List
from decimal import Decimal

from mnos.modules.admiralda.schemas import (
    CommandExecutionResult, ParsedVoiceCommand, VerifiedActor,
    PolicyDecision, FcePrecheckResult, ModuleExecutionResult, ShadowCommitResult
)
from mnos.modules.fce import service as fce_service
from mnos.modules.shadow import service as shadow_service
from mnos.core.events.dispatcher import event_dispatcher

class AmbiguousCommandError(Exception):
    pass

class AdmiraldaService:
    def __init__(self, db_session=None):
        self.db = db_session
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

        # Initial empty state for failure stubs
        parsed_intent = "UNKNOWN"
        normalized_text = transcript.strip()
        target_module = "UNKNOWN"

        try:
            # 1. Parse (Threshold >= 0.95)
            parsed = await self.parse_voice_command(transcript)
            parsed_intent = parsed.intent
            normalized_text = parsed.normalized_text
            target_module = parsed.target_module

            if parsed.confidence < 0.95:
                 return await self._fail_closed(
                     command_id, session_id, transcript, normalized_text,
                     parsed_intent, target_module, "LOW_NLU_CONFIDENCE",
                     "I'm sorry, I'm not confident enough in that request to execute it."
                 )

            # 2. Verify actor with AEGIS (Voiceprint >= 0.96)
            actor = await self.verify_actor_with_aegis(
                caller_id=caller_id,
                session_id=session_id,
                metadata=metadata,
            )

            if actor.verification_confidence < 0.96:
                 return await self._fail_closed(
                     command_id, session_id, transcript, normalized_text,
                     parsed_intent, target_module, "LOW_VOICEPRINT_CONFIDENCE",
                     "I could not verify your identity with enough certainty."
                 )

            # 3. Authorize command
            policy = await self.authorize_command(actor, parsed)
            if not policy.allowed:
                return await self._fail_closed(
                     command_id, session_id, transcript, normalized_text,
                     parsed_intent, target_module, policy.reason_code or "UNAUTHORIZED",
                     "You are not authorized for that command.", actor.actor_id
                 )

            # 4. Run FCE precheck if needed
            fce_result = None
            if parsed.requires_fce:
                # Command #1: Preauthorize amount check
                if not fce_service.preauthorize(self.db, actor.actor_id, parsed.estimated_amount or 0):
                    return await self._fail_closed(
                        command_id, session_id, transcript, normalized_text,
                        parsed_intent, target_module, "FCE_PRECHECK_FAILED",
                        "That request did not pass financial control checks.", actor.actor_id
                    )
                fce_result = FcePrecheckResult(passed=True, transaction_id=f"FCE-PRE-{uuid.uuid4().hex[:8]}")

            # 5. Dispatch to target module
            module_result = await self.dispatch_to_module(actor, parsed, fce_result)
            if not module_result.success:
                 return await self._fail_closed(
                     command_id, session_id, transcript, normalized_text,
                     parsed_intent, target_module, "MODULE_EXECUTION_FAILED",
                     module_result.human_message, actor.actor_id
                 )

            # 6. Commit to SHADOW (MANDATORY FOR SUCCESS)
            shadow = await self.commit_shadow_record(actor, parsed, module_result, fce_result)
            if not shadow.success:
                 return await self._fail_closed(
                     command_id, session_id, transcript, normalized_text,
                     parsed_intent, target_module, "SHADOW_COMMIT_FAILURE",
                     "The command was completed but could not be audited safely.", actor.actor_id
                 )

            # 7. Emit events
            events = await self.emit_events(shadow, module_result)

            return CommandExecutionResult(
                status="accepted",
                command_id=command_id,
                actor_id=actor.actor_id,
                session_id=session_id,
                transcript=transcript,
                normalized_text=normalized_text,
                intent=parsed_intent,
                target_module=target_module,
                policy_decision="allow",
                requires_fce=parsed.requires_fce,
                fce_check_passed=(True if fce_result else None),
                shadow_commit_id=shadow.commit_id,
                events_emitted=events,
                execution_payload=module_result.payload,
                human_message=module_result.human_message,
            )

        except AmbiguousCommandError:
            return await self._fail_closed(
                command_id, session_id, transcript, normalized_text,
                parsed_intent, target_module, "AMBIGUOUS_COMMAND",
                "I understood the request only partially, so I did not execute it."
            )
        except Exception as e:
            logging.exception(f"Unhandled execution failure for command {command_id}")
            return await self._fail_closed(
                command_id, session_id, transcript, normalized_text,
                parsed_intent, target_module, "UNHANDLED_EXECUTION_FAILURE",
                "The command could not be completed safely."
            )

    async def _fail_closed(self, command_id, session_id, transcript, normalized, intent, module, reason, message, actor_id=None):
        """
        Sovereign rule: Every failure path must write an audit record to SHADOW.
        """
        if self.db:
            audit_payload = {
                "command_id": command_id,
                "transcript_hash": hashlib.sha256(transcript.encode()).hexdigest(),
                "status": "REJECTED/FAILED",
                "reason_code": reason,
                "actor_id": actor_id
            }
            try:
                shadow_service.commit_evidence(self.db, f"FAIL-{command_id}", audit_payload)
                # Note: commit_evidence no longer commits, so we must commit here if we want failures persisted immediately
                # but usually failures happen outside a successful business transaction, so we commit the failure audit.
                self.db.commit()
            except:
                self.db.rollback()

        return CommandExecutionResult(
            status="rejected" if reason in ["AMBIGUOUS_COMMAND", "UNAUTHORIZED", "LOW_NLU_CONFIDENCE"] else "failed",
            command_id=command_id,
            actor_id=actor_id,
            session_id=session_id,
            transcript=transcript,
            normalized_text=normalized,
            intent=intent,
            target_module=module,
            policy_decision="deny",
            reason_code=reason,
            human_message=message
        )

    async def parse_voice_command(self, transcript: str) -> ParsedVoiceCommand:
        normalized = transcript.lower().strip()
        if not normalized:
            raise AmbiguousCommandError("Empty transcript")

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
                estimated_amount=Decimal("150.00"),
                risk_level="medium"
            )
        elif any(word in normalized for word in ["room status", "cleaned"]):
            return ParsedVoiceCommand(
                normalized_text=normalized,
                intent="room.status_inquiry",
                confidence=0.97,
                target_module="INN",
                requires_fce=False
            )
        elif any(word in normalized for word in ["fix", "broken", "maintenance"]):
            return ParsedVoiceCommand(
                normalized_text=normalized,
                intent="maintenance.ticket_create",
                confidence=0.96,
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

        raise AmbiguousCommandError("Intent not recognized")

    async def verify_actor_with_aegis(
        self,
        caller_id: str | None,
        session_id: str,
        metadata: dict | None = None,
    ) -> VerifiedActor:
        if not session_id or session_id == "EXPIRED":
            raise Exception("AEGIS: Invalid or expired session")

        confidence = 0.99
        if metadata and "voice_match_score" in metadata:
            confidence = metadata["voice_match_score"]

        return VerifiedActor(
            actor_id="ACTOR-007",
            tenant_id="TENANT-MALDIVES-OG",
            property_id="PROP-SALA",
            roles=["agent", "guest_service"],
            auth_strength="standard",
            verification_confidence=confidence
        )

    async def authorize_command(
        self,
        actor: VerifiedActor,
        cmd: ParsedVoiceCommand,
    ) -> PolicyDecision:
        if cmd.risk_level == "high" and "supervisor" not in actor.roles:
            return PolicyDecision(allowed=False, decision="deny", reason_code="INSUFFICIENT_PERMISSIONS")

        if actor.tenant_id != "TENANT-MALDIVES-OG":
             return PolicyDecision(allowed=False, decision="deny", reason_code="TENANT_MISMATCH")

        return PolicyDecision(allowed=True, decision="allow")

    async def dispatch_to_module(
        self,
        actor: VerifiedActor,
        cmd: ParsedVoiceCommand,
        fce_result: FcePrecheckResult | None = None,
    ) -> ModuleExecutionResult:
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
        evidence_payload = {
            "actor_id": actor.actor_id,
            "transcript_hash": hashlib.sha384(cmd.normalized_text.encode()).hexdigest(),
            "intent": cmd.intent,
            "module_result": module_result.success,
            "fce_tx": fce_result.transaction_id if fce_result else None
        }

        try:
            if self.db:
                 shadow_service.commit_evidence(self.db, str(uuid.uuid4()), evidence_payload)
                 self.db.commit() # Commit successful execution + shadow audit

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

        event_dispatcher.dispatch(main_event, {
            "shadow_id": shadow.commit_id,
            "payload": module_result.payload
        })

        return events
