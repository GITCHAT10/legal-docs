from decimal import Decimal

class FCEEngine:
    """
    Financial Control Engine (FCE): Authority for local Maldives economy.
    """
    SERVICE_CHARGE = Decimal("0.10")  # 10%
    TGST = Decimal("0.17")          # 17% (Tourism GST)
    GGST = Decimal("0.08")          # 8% (General GST for locals)
    COMMISSION_RATE = Decimal("0.05") # 5% default
    GREEN_TAX_USD = Decimal("6.00") # $6 per pax per night

    def calculate_order_total(self, base_price: Decimal, is_tourism: bool = False, pax: int = 0, nights: int = 0) -> dict:
        service_charge_amt = base_price * self.SERVICE_CHARGE
        subtotal = base_price + service_charge_amt

        tax_rate = self.TGST if is_tourism else self.GGST
        tax_amt = subtotal * tax_rate

        total = subtotal + tax_amt

        green_tax = Decimal("0")
        if is_tourism and pax > 0 and nights > 0:
            green_tax = self.GREEN_TAX_USD * pax * nights
            total += green_tax

        return {
            "base_price": float(base_price),
            "service_charge": float(service_charge_amt),
            "subtotal": float(subtotal),
            "tax": float(tax_amt),
            "green_tax": float(green_tax),
            "total": float(total)
        }

    def calculate_local_order(self, base_price: Decimal) -> dict:
        return self.calculate_order_total(base_price, is_tourism=False)

    def calculate_isky_commission(self, booking_amount: Decimal) -> dict:
        setup_fee = Decimal("100.00") # USD
        commission = booking_amount * self.COMMISSION_RATE
        return {
            "setup_fee": float(setup_fee),
            "commission": float(commission),
            "net_payout": float(booking_amount - commission)
        }

    def calculate_installments(self, total: Decimal, months: int) -> list:
        if months <= 0:
            return []
        monthly_amt = total / months
        schedule = []
        for i in range(1, months + 1):
            schedule.append({
                "month": i,
                "amount": float(monthly_amt.quantize(Decimal("0.01")))
            })
        return schedule
