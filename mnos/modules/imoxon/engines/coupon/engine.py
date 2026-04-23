class CouponEngine:
    def __init__(self, guard, fce, shadow, events):
        self.guard = guard
        self.fce = fce
        self.shadow = shadow
        self.events = events
        self.coupons = {}

    def create_campaign(self, actor_ctx: dict, campaign_data: dict):
        return self.guard.execute_sovereign_action(
            "imoxon.coupon.create",
            actor_ctx,
            self._internal_create_campaign,
            campaign_data
        )

    def _internal_create_campaign(self, data: dict):
        coupon_code = data.get("code")
        self.coupons[coupon_code] = {
            "discount": data.get("discount", 0.1),
            "expiry": data.get("expiry"),
            "status": "ACTIVE"
        }
        self.events.publish("coupon.campaign_created", {"code": coupon_code})
        return self.coupons[coupon_code]

    def validate_coupon(self, code: str):
        if code in self.coupons and self.coupons[code]["status"] == "ACTIVE":
            return self.coupons[code]
        return None
