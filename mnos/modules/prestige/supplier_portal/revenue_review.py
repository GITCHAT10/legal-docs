from .models import RateApprovalStatus
from mnos.shared.exceptions import ExecutionValidationError

class RevenueReviewManager:
    def review(self, rate, decision):
        if rate.approval_status != RateApprovalStatus.FINANCE_APPROVED:
            raise ExecutionValidationError("Finance approval required first")
        if decision == "APPROVE":
            rate.approval_status = RateApprovalStatus.REVENUE_APPROVED
        else:
            rate.approval_status = RateApprovalStatus.REJECTED
        return rate
