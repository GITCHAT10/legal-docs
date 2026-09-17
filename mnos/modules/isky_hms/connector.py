class iSkyCloudHMSConnector:
    """
    Hospitality SaaS Connector for iSKY Cloud HMS.
    Managed by local operators via IMOXON business dashboard.
    """
    def __init__(self, fce, shadow, events):
        self.fce = fce
        self.shadow = shadow
        self.events = events

    def activate_hms(self, operator_id: str):
        # Rule: Setup fee = 100 USD equivalent via FCE
        split = self.fce.calculate_isky_split(0.0)
        activation = {
            "operator_id": operator_id,
            "setup_fee": split["setup_fee"],
            "status": "ACTIVE"
        }
        self.shadow.record_action("isky.activation", activation)
        self.events.trigger("ISKY_HMS_ACTIVATED", activation)
        return activation

    def process_tourist_booking(self, operator_id: str, booking_amount: float):
        # Commissions calculated via FCE
        split = self.fce.calculate_isky_split(booking_amount)
        record = {
            "operator_id": operator_id,
            "amount": booking_amount,
            "split": split,
            "timestamp": "now"
        }
        self.shadow.record_action("isky.booking", record)
        return record
