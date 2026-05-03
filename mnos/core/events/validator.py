import json
import jsonschema
import re
from pathlib import Path
from mnos.core.events.namespace_mapping import validate_namespace

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schema" / "mnos_event_schema_v1_1.json"

with SCHEMA_PATH.open("r", encoding="utf-8") as f:
    MNOS_SCHEMA_V1_1 = json.load(f)

def validate_event(event: dict):
    # 1. JSON Schema Validation
    try:
        jsonschema.validate(instance=event, schema=MNOS_SCHEMA_V1_1)
    except jsonschema.ValidationError as e:
        return False, f"Schema validation failed: {e.message}"

    # 2. Namespace Validation
    system = event["source"]["system"]
    event_type = event["event_type"]
    if not validate_namespace(system, event_type):
        return False, f"Namespace mismatch: System {system} cannot emit event type {event_type}"

    # 3. Conditional Rules (PHASE 1 - Req 8)

    # FCE settlement events require proof.fce_settlement_ref when final settlement is emitted.
    if event_type.endswith(".SETTLEMENT.COMPLETE") or event_type.endswith(".SETTLED"):
         if not event["proof"].get("fce_settlement_ref"):
             return False, "Missing fce_settlement_ref for settlement event"

    # ORCA events require proof.orca_validation
    if event_type.startswith("ORCA."):
        if not event["proof"].get("orca_validation"):
            return False, "Missing orca_validation for ORCA event"

    # QRD.LAUNCH.APPROVE requires actor.device_id + proof.orca_validation.
    if event_type == "QRD.LAUNCH.APPROVE":
        if not event["actor"].get("device_id"):
            return False, "Missing device_id for QRD.LAUNCH.APPROVE"
        if not event["proof"].get("orca_validation"):
            return False, "Missing orca_validation for QRD.LAUNCH.APPROVE"

    # ADMIRALDA.ACTION.* and ADMIRALDA.DISPATCH.* require payload.consent_confirmed == true.
    if event_type.startswith("ADMIRALDA.ACTION.") or event_type.startswith("ADMIRALDA.DISPATCH."):
        if event["payload"].get("consent_confirmed") is not True:
            return False, "Consent not confirmed for ADMIRALDA event"

    # EXMAIL.NOTICE.DISPATCH requires payload.delivery_channel + payload.recipient_ref.
    if event_type == "EXMAIL.NOTICE.DISPATCH":
        if not event["payload"].get("delivery_channel") or not event["payload"].get("recipient_ref"):
            return False, "Missing delivery_channel or recipient_ref for EXMAIL notice"

    # ESG.CLAIM.VERIFY requires proof.shadow_chain_ref.
    if event_type == "ESG.CLAIM.VERIFY":
        if not event["proof"].get("shadow_chain_ref"):
            return False, "Missing shadow_chain_ref for ESG.CLAIM.VERIFY"

    # WIFI.ACCESS.GRANT with ADMIN role requires actor.device_id.
    if event_type == "WIFI.ACCESS.GRANT":
        if event["actor"].get("role") == "ADMIN" and not event["actor"].get("device_id"):
            return False, "Missing device_id for WIFI.ACCESS.GRANT (ADMIN)"

    # ISOLATION.TENANT.* requires context.tenant.brand, context.tenant.tin, context.tenant.jurisdiction.
    if event_type.startswith("ISOLATION.TENANT."):
        tenant = event.get("context", {}).get("tenant", {})
        if not tenant.get("brand") or not tenant.get("tin") or not tenant.get("jurisdiction"):
            return False, "Missing tenant context (brand, tin, jurisdiction) for ISOLATION event"

    # PEOPLE.DUTY.ASSIGN requires payload.target_staff_ref.
    if event_type == "PEOPLE.DUTY.ASSIGN":
        if not event["payload"].get("target_staff_ref"):
            return False, "Missing target_staff_ref for PEOPLE.DUTY.ASSIGN"

    # RESTRICTED / P3 / P4 events require metadata.encryption.
    # Assuming event_type or some metadata field indicates restriction level
    # Requirements say "RESTRICTED / P3 / P4 events". Let's check event_type or metadata.
    if "RESTRICTED" in event_type or event["metadata"].get("sensitivity") in ["P3", "P4"]:
        if not event["metadata"].get("encryption"):
            return False, "Encryption required for restricted event"

    return True, "Valid"
