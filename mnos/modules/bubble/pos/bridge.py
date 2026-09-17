class BubbleBPEBridge:
    """
    Bridge between BUBBLE (Core Brain) and BUBBLE POS Engine (BPE).
    """
    def __init__(self, bubble_core, bpe_engine):
        self.bubble = bubble_core
        self.bpe = bpe_engine

    def execute_order_flow(self, actor_ctx: dict, order_data: dict):
        """
        Flow: BUBBLE -> BPE -> MNOS
        """
        # 1. BUBBLE pricing decision/confirmation
        # 2. BPE Invoice creation
        merchant_id = order_data.get("vendor_id")
        invoice = self.bpe.create_invoice(merchant_id, order_data)

        # 3. BPE Stock deduction
        for item in order_data.get("items", []):
             self.bpe.update_inventory(merchant_id, item["id"], item["qty"], action="DEDUCT")

        return {
            "invoice_id": invoice["invoice_id"],
            "status": "EXECUTED",
            "pricing": invoice["pricing"]
        }
