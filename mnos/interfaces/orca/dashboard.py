class OrcaDashboard:
    def __init__(self, shadow):
        self.shadow = shadow

    def get_live_metrics(self):
        chain = self.shadow.chain
        total_revenue = 0
        for block in chain:
            if block["event_type"] == "upos.order.completed":
                total_revenue += block["payload"]["pricing"]["total"]

        return {
            "total_revenue": total_revenue,
            "order_count": len([b for b in chain if b["event_type"] == "upos.order.completed"]),
            "integrity": self.shadow.verify_integrity()
        }
