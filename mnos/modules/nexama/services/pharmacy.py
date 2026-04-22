from typing import List, Dict, Any
from mnos.shared.sdk.client import mnos_client

class PharmacyService:
    async def validate_prescription(self, patient_id: str, prescriptions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Enforces drug safety guardrails: Allergy conflicts, drug interactions, pregnancy contraindications.
        """
        # 1. Fetch Patient Context (including Maternal risk)
        # Mocking patient data fetch via MNOS client
        patient_context = {
            "is_maternal_risk": True,
            "allergies": ["penicillin"],
            "current_medications": ["aspirin"]
        }

        violations = []
        for drug in prescriptions:
            drug_name = drug.get("name", "").lower()

            # Check Allergies
            if drug_name in patient_context["allergies"]:
                violations.append(f"ALLERGY_CONFLICT: Patient is allergic to {drug_name}")

            # Check Pregnancy Contraindications
            if patient_context["is_maternal_risk"] and self._is_pregnancy_contraindicated(drug_name):
                violations.append(f"PREGNANCY_CONTRAINDICATION: {drug_name} is unsafe during pregnancy")

            # Check Drug Interactions
            if self._has_interaction(drug_name, patient_context["current_medications"]):
                violations.append(f"DRUG_INTERACTION: {drug_name} interacts with current medications")

        if violations:
            return {
                "status": "BLOCKED",
                "violations": violations,
                "requires_override": False
            }

        return {"status": "VALIDATED", "violations": []}

    def _is_pregnancy_contraindicated(self, drug_name: str) -> bool:
        # Mock database of contraindications
        unsafe_drugs = ["warfarin", "isotretinoin", "methotrexate", "ciprofloxacin"]
        return drug_name in unsafe_drugs

    def _has_interaction(self, new_drug: str, current_drugs: List[str]) -> bool:
        # Mock interaction logic
        interactions = {("warfarin", "aspirin"), ("sildenafil", "nitroglycerin")}
        for current in current_drugs:
            if (new_drug, current) in interactions or (current, new_drug) in interactions:
                return True
        return False

pharmacy_service = PharmacyService()
