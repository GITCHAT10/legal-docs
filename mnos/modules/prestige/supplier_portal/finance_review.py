from .models import RateApprovalStatus

class FinanceReviewManager:
    def review(self, rate, decision):
        if decision == "APPROVE":
            rate.approval_status = RateApprovalStatus.FINANCE_APPROVED
        else:
            rate.approval_status = RateApprovalStatus.REJECTED
        return rate
