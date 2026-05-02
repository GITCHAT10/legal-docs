from .models import RateApprovalStatus
from mnos.shared.exceptions import ExecutionValidationError

class CMOMarketStrategyManager:
    def approve_for_market(self, rate, decision):
        if rate.approval_status != RateApprovalStatus.REVENUE_APPROVED:
            raise ExecutionValidationError("Revenue approval required first")
        if decision == "APPROVE":
            rate.approval_status = RateApprovalStatus.CMO_APPROVED_FOR_MARKET
        else:
            rate.approval_status = RateApprovalStatus.REJECTED
        return rate
