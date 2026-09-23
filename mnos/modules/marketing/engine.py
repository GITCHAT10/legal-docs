import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional


class SovereignMarketingEngine:
    """MIG multi-brand marketing, attribution and approval control plane.

    External publisher/ad-network connectors remain adapters. This domain engine
    owns campaign state, approval gates, spend controls, lead attribution and
    immutable SHADOW audit events.
    """

    APPROVER_ROLES = {"admin", "system_admin", "finance_mgr", "marketing_director", "group_cfo"}
    OPERATOR_ROLES = APPROVER_ROLES | {"marketing_manager", "marketing_operator", "sales"}

    def __init__(self, core: Any):
        self.core = core
        self.brands: Dict[str, dict] = {}
        self.campaigns: Dict[str, dict] = {}
        self.content_items: Dict[str, dict] = {}
        self.leads: Dict[str, dict] = {}
        self.conversions: Dict[str, dict] = {}

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _id(prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4().hex[:10].upper()}"

    @staticmethod
    def _role(actor: dict) -> str:
        return str(actor.get("role") or "").lower()

    def _require(self, actor: dict, allowed: set[str]) -> None:
        if self._role(actor) not in allowed:
            raise PermissionError("MARKETING_ACCESS_DENIED")

    def _execute(self, action: str, actor: dict, fn, *args):
        return self.core.execute_commerce_action(action, actor, fn, *args)

    def register_brand(self, actor: dict, data: dict) -> dict:
        self._require(actor, self.APPROVER_ROLES)
        return self._execute("marketing.brand.register", actor, self._register_brand, data, actor)

    def _register_brand(self, data: dict, actor: dict) -> dict:
        name = str(data.get("name") or "").strip()
        if not name:
            raise ValueError("Brand name is required")
        brand_id = self._id("BRAND")
        brand = {
            "id": brand_id,
            "name": name,
            "legal_entity_id": data.get("legal_entity_id"),
            "voice": data.get("voice", {}),
            "markets": data.get("markets", []),
            "languages": data.get("languages", ["en"]),
            "approval_policy": data.get("approval_policy", "HUMAN_APPROVAL"),
            "status": "ACTIVE",
            "created_by": actor.get("identity_id"),
            "created_at": self._now(),
        }
        self.brands[brand_id] = brand
        return brand

    def create_campaign(self, actor: dict, data: dict) -> dict:
        self._require(actor, self.OPERATOR_ROLES)
        return self._execute("marketing.campaign.create", actor, self._create_campaign, data, actor)

    def _create_campaign(self, data: dict, actor: dict) -> dict:
        brand_id = data.get("brand_id")
        if brand_id not in self.brands:
            raise ValueError("Brand not found")
        budget = Decimal(str(data.get("budget", "0")))
        if budget < 0:
            raise ValueError("Campaign budget cannot be negative")
        campaign_id = self._id("CMP")
        campaign = {
            "id": campaign_id,
            "brand_id": brand_id,
            "name": str(data.get("name") or "Untitled Campaign"),
            "objective": data.get("objective", "AWARENESS"),
            "channels": data.get("channels", []),
            "markets": data.get("markets", []),
            "currency": data.get("currency", "USD"),
            "budget": str(budget.quantize(Decimal("0.01"))),
            "spend": "0.00",
            "status": "DRAFT",
            "approval": None,
            "created_by": actor.get("identity_id"),
            "created_at": self._now(),
        }
        self.campaigns[campaign_id] = campaign
        return campaign

    def submit_campaign(self, actor: dict, campaign_id: str) -> dict:
        self._require(actor, self.OPERATOR_ROLES)
        return self._execute("marketing.campaign.submit", actor, self._submit_campaign, campaign_id)

    def _submit_campaign(self, campaign_id: str) -> dict:
        campaign = self._campaign(campaign_id)
        if campaign["status"] not in {"DRAFT", "REJECTED"}:
            raise ValueError("Only draft or rejected campaigns may be submitted")
        campaign["status"] = "PENDING_APPROVAL"
        campaign["submitted_at"] = self._now()
        return campaign

    def approve_campaign(self, actor: dict, campaign_id: str, decision: str, reason: Optional[str] = None) -> dict:
        self._require(actor, self.APPROVER_ROLES)
        return self._execute(
            "marketing.campaign.approve", actor, self._approve_campaign,
            campaign_id, decision.upper(), reason, actor,
        )

    def _approve_campaign(self, campaign_id: str, decision: str, reason: Optional[str], actor: dict) -> dict:
        campaign = self._campaign(campaign_id)
        if campaign["status"] != "PENDING_APPROVAL":
            raise ValueError("Campaign is not pending approval")
        if decision not in {"APPROVE", "REJECT"}:
            raise ValueError("Decision must be APPROVE or REJECT")
        campaign["status"] = "APPROVED" if decision == "APPROVE" else "REJECTED"
        campaign["approval"] = {
            "decision": decision,
            "reason": reason,
            "actor_id": actor.get("identity_id"),
            "timestamp": self._now(),
        }
        return campaign

    def activate_campaign(self, actor: dict, campaign_id: str) -> dict:
        self._require(actor, self.OPERATOR_ROLES)
        return self._execute("marketing.campaign.activate", actor, self._activate_campaign, campaign_id)

    def _activate_campaign(self, campaign_id: str) -> dict:
        campaign = self._campaign(campaign_id)
        if campaign["status"] != "APPROVED":
            raise ValueError("Campaign must be approved before activation")
        campaign["status"] = "ACTIVE"
        campaign["activated_at"] = self._now()
        return campaign

    def record_spend(self, actor: dict, campaign_id: str, amount: Decimal, external_ref: str) -> dict:
        self._require(actor, self.APPROVER_ROLES)
        return self._execute(
            "marketing.spend.record", actor, self._record_spend,
            campaign_id, Decimal(str(amount)), external_ref,
        )

    def _record_spend(self, campaign_id: str, amount: Decimal, external_ref: str) -> dict:
        campaign = self._campaign(campaign_id)
        if campaign["status"] not in {"ACTIVE", "PAUSED"}:
            raise ValueError("Spend can only be recorded for active or paused campaigns")
        if amount <= 0:
            raise ValueError("Spend amount must be positive")
        current = Decimal(campaign["spend"])
        budget = Decimal(campaign["budget"])
        updated = current + amount
        if updated > budget:
            raise ValueError("Campaign budget exceeded")
        campaign["spend"] = str(updated.quantize(Decimal("0.01")))
        campaign.setdefault("spend_events", []).append({
            "amount": str(amount.quantize(Decimal("0.01"))),
            "external_ref": external_ref,
            "timestamp": self._now(),
        })
        return campaign

    def create_content(self, actor: dict, data: dict) -> dict:
        self._require(actor, self.OPERATOR_ROLES)
        return self._execute("marketing.content.create", actor, self._create_content, data, actor)

    def _create_content(self, data: dict, actor: dict) -> dict:
        campaign = self._campaign(data.get("campaign_id"))
        content_id = self._id("CONTENT")
        item = {
            "id": content_id,
            "campaign_id": campaign["id"],
            "channel": data.get("channel"),
            "language": data.get("language", "en"),
            "copy": data.get("copy", ""),
            "asset_refs": data.get("asset_refs", []),
            "status": "DRAFT",
            "created_by": actor.get("identity_id"),
            "created_at": self._now(),
        }
        self.content_items[content_id] = item
        return item

    def capture_lead(self, actor: dict, data: dict) -> dict:
        self._campaign(data.get("campaign_id"))
        return self._execute("marketing.lead.capture", actor, self._capture_lead, data)

    def _capture_lead(self, data: dict) -> dict:
        lead_id = self._id("LEAD")
        lead = {
            "id": lead_id,
            "campaign_id": data.get("campaign_id"),
            "source": data.get("source"),
            "market": data.get("market"),
            "consent": bool(data.get("consent", False)),
            "external_contact_ref": data.get("external_contact_ref"),
            "status": "NEW",
            "created_at": self._now(),
        }
        self.leads[lead_id] = lead
        return lead

    def record_conversion(self, actor: dict, data: dict) -> dict:
        self._require(actor, self.OPERATOR_ROLES)
        return self._execute("marketing.conversion.record", actor, self._record_conversion, data)

    def _record_conversion(self, data: dict) -> dict:
        campaign = self._campaign(data.get("campaign_id"))
        revenue = Decimal(str(data.get("revenue", "0")))
        if revenue < 0:
            raise ValueError("Revenue cannot be negative")
        conversion_id = self._id("CNV")
        conversion = {
            "id": conversion_id,
            "campaign_id": campaign["id"],
            "lead_id": data.get("lead_id"),
            "booking_ref": data.get("booking_ref"),
            "ledger_entry_ref": data.get("ledger_entry_ref"),
            "currency": data.get("currency", campaign["currency"]),
            "revenue": str(revenue.quantize(Decimal("0.01"))),
            "created_at": self._now(),
        }
        self.conversions[conversion_id] = conversion
        return conversion

    def dashboard(self, actor: dict, brand_id: Optional[str] = None) -> dict:
        self._require(actor, self.OPERATOR_ROLES)
        campaigns = [c for c in self.campaigns.values() if not brand_id or c["brand_id"] == brand_id]
        campaign_ids = {c["id"] for c in campaigns}
        conversions = [c for c in self.conversions.values() if c["campaign_id"] in campaign_ids]
        leads = [l for l in self.leads.values() if l["campaign_id"] in campaign_ids]
        spend = sum((Decimal(c["spend"]) for c in campaigns), Decimal("0"))
        revenue = sum((Decimal(c["revenue"]) for c in conversions), Decimal("0"))
        roas = (revenue / spend) if spend else Decimal("0")
        return {
            "campaigns": len(campaigns),
            "active_campaigns": sum(1 for c in campaigns if c["status"] == "ACTIVE"),
            "leads": len(leads),
            "conversions": len(conversions),
            "spend": str(spend.quantize(Decimal("0.01"))),
            "attributed_revenue": str(revenue.quantize(Decimal("0.01"))),
            "roas": str(roas.quantize(Decimal("0.01"))),
        }

    def _campaign(self, campaign_id: str) -> dict:
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")
        return campaign
