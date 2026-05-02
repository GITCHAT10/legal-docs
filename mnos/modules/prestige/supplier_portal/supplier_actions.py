import uuid
from typing import Dict, Any, List
from .models import MarketSellingRate, RateApprovalStatus, VisibilityScope, ChannelType
from mnos.shared.exceptions import ExecutionValidationError
from .finance_review import FinanceReviewManager
from .revenue_review import RevenueReviewManager
from .cmo_market_strategy import CMOMarketStrategyManager
from .stop_sell_manager import StopSellManager
from .contract_upload import ContractUploadManager
from .specials_manager import SpecialsManager
from .open_sale_manager import OpenSaleManager
from .allotment_manager import AllotmentManager
from .admin_notifications import AdminNotificationSystem

class PrestigeSupplierPortal:
    """
    Universal PH Supplier Portal for Maldives Resorts.
    Governs the end-to-end commercial lifecycle of hospitality rates.
    """
    def __init__(self, guard, shadow, events, fce, market_engine):
        self.guard = guard
        self.shadow = shadow
        self.events = events
        self.fce = fce
        self.market_engine = market_engine

        # Managers
        self.finance = FinanceReviewManager()
        self.revenue = RevenueReviewManager()
        self.cmo = CMOMarketStrategyManager()
        self.stop_sell_mgr = StopSellManager(shadow)
        self.contract_mgr = ContractUploadManager(shadow)
        self.specials_mgr = SpecialsManager(shadow)
        self.open_sale_mgr = OpenSaleManager()
        self.allotment_mgr = AllotmentManager()
        self.notifier = AdminNotificationSystem()

        self.rates: Dict[str, MarketSellingRate] = {}

    def upload_contract_pdf(self, actor_ctx: dict, supplier_id: str, resort_name: str, file_name: str):
        def _execute_upload():
            res = self.contract_mgr.handle_upload(actor_ctx, supplier_id, resort_name, file_name)
            self.notifier.notify_admin("CONTRACT_UPLOADED", res)
            return {"status": "AI_EXTRACTED_DRAFT", "trace_id": res["trace_id"]}
        return self.guard.execute_sovereign_action("prestige.supplier.contract_upload", actor_ctx, _execute_upload)

    def submit_rate_sheet(self, actor_ctx: dict, payload: dict):
        def _execute_submit():
            trace_id = payload.get("trace_id", str(uuid.uuid4().hex[:8]))
            strategy = {"EU_markup_percent": 0.35, "revenue_margin_floor": 0.15}
            rate = self.market_engine.generate_rates(actor_ctx, payload, strategy)
            self.rates[rate.rate_id] = rate
            self.shadow.commit("prestige.supplier.rate_sheet_uploaded", actor_ctx["identity_id"], {
                "trace_id": trace_id, "rate_id": rate.rate_id
            })
            self.notifier.notify_admin("RATE_SHEET_SUBMITTED", {"rate_id": rate.rate_id})
            return rate.model_dump()
        return self.guard.execute_sovereign_action("prestige.supplier.rate_submit", actor_ctx, _execute_submit)

    def approve_stage(self, actor_ctx: dict, rate_id: str, stage: str, decision: str):
        rate = self.rates.get(rate_id)
        if not rate:
             raise ExecutionValidationError(f"RATE_NOT_FOUND: {rate_id}")

        def _execute_approval():
            role = actor_ctx.get("role")
            if stage == "FINANCE":
                if role not in ["finance_reviewer", "mac_eos_admin"]:
                    raise PermissionError("Role finance_reviewer required")
                self.finance.review(rate, decision)

            elif stage == "REVENUE":
                if role not in ["revenue_reviewer", "mac_eos_admin"]:
                    raise PermissionError("Role revenue_reviewer required")
                self.revenue.review(rate, decision)

            elif stage == "CMO":
                if role not in ["cmo_reviewer", "mac_eos_admin"]:
                    raise PermissionError("Role cmo_reviewer required")
                self.cmo.approve_for_market(rate, decision)

                if decision == "APPROVE":
                    self._verify_channel_gates(rate)
                    rate.approval_status = RateApprovalStatus.ACTIVE_FOR_SALE
                    rate.safe_to_publish = True
                    seal = self.shadow.commit("prestige.supplier.shadow_sealed", "SYSTEM", {
                        "trace_id": rate.trace_id, "rate_id": rate_id
                    })
                    rate.audit_seal = seal

            self.notifier.notify_admin(f"RATE_APPROVAL_{stage}", {"rate_id": rate_id, "decision": decision})
            return rate.model_dump()
        return self.guard.execute_sovereign_action(f"prestige.supplier.approve.{stage.lower()}", actor_ctx, _execute_approval)

    def stop_sell(self, actor_ctx: dict, product_id: str):
        def _execute_stop():
            res = self.stop_sell_mgr.apply_stop_sell(actor_ctx, product_id)
            self.notifier.notify_admin("STOP_SELL_ACTIVATED", res)
            return res
        return self.guard.execute_sovereign_action("prestige.supplier.stop_sell", actor_ctx, _execute_stop)

    def submit_special(self, actor_ctx, payload):
        def _execute_special():
             return self.specials_mgr.submit_special(actor_ctx, payload)
        return self.guard.execute_sovereign_action("prestige.supplier.special_submit", actor_ctx, _execute_special)

    def request_open_sale(self, product_id):
        # Open sale usually needs approval too, but let's keep it simple for now
        return self.open_sale_mgr.request_open_sale(product_id)

    def update_allotment(self, product_id, count):
        return self.allotment_mgr.update_allotment(product_id, count)

    def _verify_channel_gates(self, rate: MarketSellingRate):
        if rate.channel_type == ChannelType.B2C_DIRECT and rate.visibility_scope != VisibilityScope.PUBLIC:
            raise ExecutionValidationError("B2C requires PUBLIC visibility")
        if rate.channel_type == ChannelType.B2G_GOVERNMENT and rate.visibility_scope not in [VisibilityScope.RESTRICTED, VisibilityScope.PRIVATE]:
             raise ExecutionValidationError("B2G requires RESTRICTED or PRIVATE visibility")
        if rate.channel_type in [ChannelType.VIP_PRIVATE, ChannelType.BLACK_BOOK] and rate.visibility_scope not in [VisibilityScope.P3_PRIVACY, VisibilityScope.P4_PRIVACY]:
             raise ExecutionValidationError(f"{rate.channel_type} requires P3/P4 Privacy")
        if rate.channel_type == ChannelType.B2B2C_AGENT_TO_GUEST:
            if rate.b2b2c_guest_rate <= rate.b2b_agent_net_rate:
                 raise ExecutionValidationError("B2B2C margin protection violation")

    def get_rate(self, actor_ctx: dict, rate_id: str, channel: ChannelType):
        rate = self.rates.get(rate_id)
        if not rate or not rate.safe_to_publish:
             raise ExecutionValidationError("RATE_NOT_AVAILABLE")
        if self.stop_sell_mgr.is_stopped(rate.product_id):
             raise ExecutionValidationError("STOP_SELL_IN_EFFECT")
        if rate.channel_type == ChannelType.BLACK_BOOK and actor_ctx.get("role") != "black_book_agent":
             raise PermissionError("BLACK_BOOK distribution restricted")
        return rate.model_dump()
