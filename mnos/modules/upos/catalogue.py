import uuid
from typing import Dict, List, Any, Optional

class UCatalogueEngine:
    """
    UPOS Resort Catalogue: Role-based, department-isolated visibility.
    """
    def __init__(self, shadow):
        self.shadow = shadow
        self.catalogues = {} # tenant_id -> list of items

    def get_visible_categories(self, actor_ctx: dict) -> List[str]:
        role = actor_ctx.get("role")

        # GM / Admin / Procurement can see everything
        if role in ["resort_gm", "admin", "procurement_manager", "finance_manager"]:
            return [
                "F&B", "Housekeeping", "Laundry", "Spa", "Engineering",
                "IT", "Marine", "Retail", "Medical", "Office", "Local Stock"
            ]

        # Department-based visibility
        role_map = {
            "executive_chef": ["F&B"],
            "fnb_manager": ["F&B"],
            "housekeeping_manager": ["Housekeeping", "Linen", "Laundry"],
            "spa_manager": ["Spa"],
            "engineering_manager": ["Engineering", "Utilities"],
            "it_manager": ["IT", "U-WiFi"],
            "marine_manager": ["Marine", "Transport"],
            "storekeeper": ["Local Stock", "Incoming Goods", "All Categories"]
        }

        return role_map.get(role, [])

    def browse_catalogue(self, actor_ctx: dict, tenant_id: str, category: str = None):
        # HARD GATE: Tenant isolation
        # (Assuming actor_ctx["org_id"] matches tenant_id or actor is super admin)

        visible_categories = self.get_visible_categories(actor_ctx)

        if category and category not in visible_categories:
             raise PermissionError(f"ACCESS_DENIED: Department {actor_ctx.get('role')} cannot access category {category}")

        # Simulation of filtered results
        return {
            "tenant_id": tenant_id,
            "role": actor_ctx.get("role"),
            "accessible_categories": visible_categories,
            "items": [] # Filtered items would go here
        }
