import uuid
class ContractUploadManager:
    def __init__(self, shadow):
        self.shadow = shadow
    def handle_upload(self, actor_ctx, supplier_id, resort_name, file_data):
        trace_id = str(uuid.uuid4().hex[:8])
        self.shadow.commit("prestige.supplier.contract_uploaded", actor_ctx["identity_id"], {
            "trace_id": trace_id, "supplier_id": supplier_id, "resort": resort_name
        })
        return {"status": "CONTRACT_UPLOADED", "trace_id": trace_id}
