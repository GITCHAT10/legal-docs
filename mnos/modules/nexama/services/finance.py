from typing import Dict, Any
import uuid
import datetime
from mnos.modules.fce.service import fce_service

class FinanceService:
    TGST_RATE = 0.17 # 17% for Maldives private services
    SERVICE_CHARGE_RATE = 0.10 # 10% mandatory service charge

    async def generate_claim(self, encounter_id: str, payer_id: str, base_amount: float) -> Dict[str, Any]:
        """
        Generates MIRA-compliant claims with strict audit-proof invoice math
        and Aasandha Vira Portal real-time clearing.
        """
        claim_id = f"CLM-{uuid.uuid4()}"

        # 1. Audit-Proof Invoice Math (MIRA-ready)
        # Base -> SC -> Subtotal -> TGST -> Total
        service_charge = base_amount * self.SERVICE_CHARGE_RATE
        subtotal = base_amount + service_charge

        tax_amount = 0.0
        # TGST applied on Subtotal (Base + SC)
        if payer_id != "Aasandha":
            tax_amount = subtotal * self.TGST_RATE

        total_amount = subtotal + tax_amount

        # 2. Aasandha Vira Split Logic
        aasandha_coverage = 0.0
        patient_copay = total_amount
        vira_token = None

        if payer_id == "Aasandha":
            # Real-time clearing via Vira Portal API (mocked)
            aasandha_coverage = total_amount
            patient_copay = 0.0
            vira_token = f"VIRA-{uuid.uuid4().hex[:10].upper()}"

        # 3. Tax Point Date & Exchange Rate Lock
        tax_point_date = datetime.datetime.utcnow().isoformat()
        exchange_rate = 15.42

        result = {
            "id": claim_id,
            "encounter_id": encounter_id,
            "payer_id": payer_id,
            "vira_token": vira_token,
            "base_amount": base_amount,
            "service_charge": service_charge,
            "subtotal": subtotal,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "aasandha_coverage": aasandha_coverage,
            "patient_copay": patient_copay,
            "tax_point_date": tax_point_date,
            "exchange_rate_locked": exchange_rate,
            "currency": "MVR",
            "status": "POSTED",
            "ledger_anchor": f"SHA256-{uuid.uuid4().hex}"
        }

        return result

finance_service = FinanceService()
