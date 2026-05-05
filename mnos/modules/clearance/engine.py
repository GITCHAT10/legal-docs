import uuid
from .forms import UClearanceFormsPack

class UClearanceEngine:
    """
    U-Clearance: Customs and Port document workflow and release approval.
    """
    def __init__(self, customs, port, shadow):
        self.customs = customs
        self.port = port
        self.shadow = shadow
        self.forms_pack = UClearanceFormsPack()
        self.clearance_jobs = {}

    def initiate_clearance(self, actor_ctx: dict, shipment_id: str):
        job_id = f"CLR-{uuid.uuid4().hex[:6].upper()}"
        job = {
            "id": job_id,
            "shipment_id": shipment_id,
            "status": "DOCUMENTS_PENDING",
            "required_docs": self.forms_pack.get_required_docs(),
            "uploaded_docs": {},
            "customs_released": False,
            "port_released": False
        }
        self.clearance_jobs[job_id] = job
        return job

    def upload_document(self, actor_ctx: dict, job_id: str, doc_type: str, file_hash: str):
        job = self.clearance_jobs.get(job_id)
        if doc_type not in job["required_docs"]:
             raise ValueError("Document not required for this shipment")

        job["uploaded_docs"][doc_type] = {
            "hash": file_hash,
            "uploaded_by": actor_ctx.get("identity_id"),
            "status": "UPLOADED"
        }
        return True

    def validate_documents(self, actor_ctx: dict, job_id: str):
        job = self.clearance_jobs.get(job_id)
        # Check mandatory docs
        mandatory = [k for k, v in job["required_docs"].items() if v.get("mandatory")]
        missing = [d for d in mandatory if d not in job["uploaded_docs"]]

        if not missing:
            job["status"] = "DOCUMENTS_COMPLETE"
            self.shadow.commit("clearance.documents.validated", actor_ctx.get("identity_id"), {"job_id": job_id})
        else:
            job["status"] = "DOCUMENTS_PENDING"

        return {"status": job["status"], "missing": missing}

    def approve_customs_release(self, actor_ctx: dict, job_id: str):
        job = self.clearance_jobs.get(job_id)
        # Gate: check docs status
        if job["status"] != "DOCUMENTS_COMPLETE":
             raise PermissionError("GLOBAL GATE: No Customs submission without required document checklist.")

        job["customs_released"] = True
        return job

    def approve_port_release(self, actor_ctx: dict, job_id: str):
        job = self.clearance_jobs.get(job_id)
        if not job["customs_released"]:
            raise PermissionError("DOCTRINE REJECTION: No port release without Customs release.")

        job["port_released"] = True
        job["status"] = "RELEASED_TO_WAREHOUSE"
        return job
