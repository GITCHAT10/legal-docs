from mnos.shared.guard.test_signer import aegis_sign
import sys
import os
from decimal import Decimal
import json

# Ensure PYTHONPATH
sys.path.append(os.getcwd())

from mnos.modules.fce.service import fce
from mnos.modules.shadow.service import shadow
from mnos.core.security.aegis import aegis, SecurityException


def run_proof():
    print("--- 🏛️ NEXUS ASI SKY-i OS FINAL CERTIFICATION PROOF ---")

    proof_results = {}

    # 1. AEGIS: Spoof & Binding
    print("\n[PROOF: AEGIS SECURITY]")
    try:
        # Scenario: Unauthorized device ID
        payload = {"device_id": "untrusted-hardware-X"}
        payload["signature"] = aegis_sign(payload)
        aegis.validate_session(payload)
        proof_results["aegis_spoof_rejection"] = "FAIL (Bypassed)"
    except SecurityException as e:
        print(f" -> PASSED: Blocked untrusted device: {e}")
        proof_results["aegis_spoof_rejection"] = "PASS"

    # 2. SHADOW: Genesis Tamper
    print("\n[PROOF: SHADOW INTEGRITY]")
    try:
        shadow.chain = []
        shadow._seed_ledger()
        # Tamper with genesis
        shadow.chain[0]["hash"] = "TAMPERED_HASH"
        # Attempt commit
        from mnos.shared.execution_guard import in_sovereign_context
        t = in_sovereign_context.set(True)
        try:
            shadow.commit("proof_event", {})
            proof_results["shadow_tamper_detection"] = "FAIL (Bypassed)"
        finally:
            in_sovereign_context.reset(t)
    except RuntimeError as e:
        print(f" -> PASSED: Detected ledger corruption: {e}")
        proof_results["shadow_tamper_detection"] = "PASS"

    # 3. MIRA: Maldives Scenarios
    print("\n[PROOF: MIRA COMPLIANCE]")
    # Scenario: 14h stay (should charge Green Tax)
    res1 = fce.calculate_folio(Decimal("100.00"), stay_hours=14.0)
    # Scenario: 10h stay (should NOT charge Green Tax)
    res2 = fce.calculate_folio(Decimal("100.00"), stay_hours=10.0)
    # Scenario: Child guest
    res3 = fce.calculate_folio(Decimal("100.00"), is_child=True)

    mira_ok = (res1["green_tax"] > 0 and res2["green_tax"] == 0 and res3["green_tax"] == 0)
    print(f" -> MIRA Rules Validated: {mira_ok}")
    assert mira_ok is True
    proof_results["mira_compliance"] = "PASS"

    # 4. eFaas: Identity Mapping
    print("\n[PROOF: eFaas IDENTITY]")
    oidc_sample = {
        "id_number": "A999999",
        "name": "Certified Resident",
        "birthdate": "1985-05-20",
        "email_verified": True
    }
    mapping = aegis._map_efaas_identity(oidc_sample)
    efaas_ok = (mapping["national_id"] == "A999999" and mapping["full_name"] == "Certified Resident")
    print(f" -> Identity fields confirmed: {efaas_ok}")
    assert efaas_ok is True
    proof_results["efaas_mapping"] = "PASS"

    print("\n--- PROOF SUMMARY ---")
    print(json.dumps(proof_results, indent=2))

    # Return results for report inclusion
    return proof_results

if __name__ == "__main__":
    run_proof()
