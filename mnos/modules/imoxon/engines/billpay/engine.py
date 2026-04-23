class BillPayEngine:
    """
    IMOXON PAY: Utility bill fetching and multi-payment routing.
    """
    def __init__(self, fce, shadow, events):
        self.fce = fce
        self.shadow = shadow
        self.events = events

    def fetch_bill(self, biller_id: str, account: str):
        # Simulated provider API call (STELCO/MWSC)
        return {"biller": biller_id, "account": account, "amount": 750.0}

    def pay_bill(self, user_id: str, bill: dict):
        pricing = self.fce.price_order(bill["amount"])
        payment = {
            "user": user_id,
            "biller": bill["biller"],
            "amount": pricing["total"],
            "status": "SETTLED",
            "rail": "FAVARA_RTGS"
        }
        self.shadow.commit("pay.bill_paid", payment)
        self.events.publish("PAYMENT_CAPTURED", payment)
        return payment
