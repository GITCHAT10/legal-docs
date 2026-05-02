class OpenSaleManager:
    def request_open_sale(self, product_id):
        return {"status": "OPEN_SALE_REQUESTED", "product_id": product_id}
