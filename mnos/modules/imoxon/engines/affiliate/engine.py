class AffiliateEngine:
    def __init__(self, fce, shadow):
        self.fce = fce
        self.shadow = shadow

    def track_click(self, user_id: str, product_link: str):
        event = {
            "user_id": user_id,
            "link": product_link,
            "timestamp": "now"
        }
        self.shadow.commit("affiliate.clicked", event)
        return True

    def record_external_commission(self, affiliate_id: str, sale_amount: float):
        commission = sale_amount * 0.05
        self.shadow.commit("affiliate.commission", {"id": affiliate_id, "amount": commission})
