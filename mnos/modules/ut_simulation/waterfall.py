from decimal import Decimal
class QTRevenueWaterfall:
    def calculate_waterfall(self, gross: Decimal):
        tax = (gross * Decimal("0.17")).quantize(Decimal("0.01"))
        return {"gross": gross, "tax": tax, "net": gross - tax}
waterfall_sim = QTRevenueWaterfall()
