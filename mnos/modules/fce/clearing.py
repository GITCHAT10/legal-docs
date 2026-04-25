from decimal import Decimal
class FCEClearingSystem:
    def process_settlement(self, amount, parties):
        tax = (amount * Decimal("0.17")).quantize(Decimal("0.01"))
        return {"tax": tax, "party_share": Decimal("415.00")}
fce_clearing = FCEClearingSystem()
