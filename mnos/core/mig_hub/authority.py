import uuid
from decimal import Decimal
from datetime import datetime, UTC

class MIGCoreAuthority:
    """
    MIG Identity-Payment-Tax Core
    Shared Core Service for UT, iMOXON, and ILUVIA.
    """
    def __init__(self, shadow, events, fce):
        self.shadow = shadow
        self.events = events
        self.fce = fce
        self.wallets = {} # identity_id -> {MVR, USD}

    def verify_efaas_identity(self, efaas_token: str):
        # Integration with National eFaas Service
        return {
            "identity_id": f"MIG-ID-{uuid.uuid4().hex[:6].upper()}",
            "verified": True,
            "type": "LOCAL" # LOCAL, GUEST, WORKER
        }

    def route_payment(self, actor_id: str, amount: Decimal, currency: str, source: str):
        """
        Routes payments via BML, FonePay, or ILUVIA Wallet.
        """
        # Payment rail logic
        return {
            "transaction_id": f"TX-{uuid.uuid4().hex[:8].upper()}",
            "status": "COMPLETED",
            "currency": currency,
            "rail": "BML_GATEWAY" if currency == "USD" else "ILUVIA_WALLET"
        }

    def generate_mira_report(self, transaction_id: str, tax_data: dict):
        # Logic for MIRA-ready ledger entry
        self.shadow.commit("compliance.mira.entry", "SYSTEM", {
            "tx_id": transaction_id,
            "tax_details": tax_data,
            "timestamp": datetime.now(UTC).isoformat()
        })
        return True

class UnitedTransferAPI:
    def __init__(self, mig_core):
        self.mig = mig_core

    def book_transport(self, efaas_token: str, route_id: str):
        identity = self.mig.verify_efaas_identity(efaas_token)
        # Rule: Local pays MVR, Tourist pays USD
        currency = "MVR" if identity["type"] == "LOCAL" else "USD"
        return {"identity": identity, "currency": currency}

class iMoxonTradeAPI:
    def __init__(self, mig_core):
        self.mig = mig_core

    def settle_vendor(self, vendor_id: str, amount: Decimal, buyer_currency: str):
        # Local supplier invoices in MVR, foreign buyer pays USD
        settlement = self.mig.route_payment(vendor_id, amount, "MVR", "USD_CONVERSION")
        return settlement
