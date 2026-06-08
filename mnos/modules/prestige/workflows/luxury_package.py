from typing import Dict

class LuxuryPackageWorkflow:
    def __init__(self, prestige_core, registry):
        self.prestige = prestige_core
        self.registry = registry

    async def execute_inquiry(self, actor_ctx: Dict, inquiry_data: Dict) -> Dict:
        """
        PRESTIGE First Real Workflow: Luxury Package
        Inquiry -> Planner -> Hotel Sourcing -> Pricing -> Compliance -> MAC EOS -> SHADOW
        """
        planner = self.registry.get_agent("planner")
        hotel_agent = self.registry.get_agent("hotel_agent")
        pricing_agent = self.registry.get_agent("pricing_agent")
        compliance_agent = self.registry.get_agent("compliance")

        # 1. Planner decomposes inquiry
        await planner.execute_task({"inquiry": inquiry_data.get("text")})

        # 2. Hotel Sourcing
        hotels = await hotel_agent.execute_task({
            "location": inquiry_data.get("location"),
            "dates": inquiry_data.get("dates"),
            "guests": inquiry_data.get("guests")
        })

        # FIX: Empty hotel results check
        if not hotels.get("options") or len(hotels["options"]) == 0:
            return self.prestige.core.execute_commerce_action(
                "prestige.package.no_availability",
                actor_ctx,
                self._handle_no_availability
            )

        # Select best option (mocked selection)
        best_hotel = hotels["options"][0]

        # 3. Pricing Agent calculates package
        pricing = await pricing_agent.execute_task({
            "base_price_usd": best_hotel["rate_usd"],
            "nights": inquiry_data.get("nights", 1),
            "adults": inquiry_data.get("guests", 1)
        })

        # 4. Compliance Agent checks rules
        compliance = await compliance_agent.execute_task(pricing)

        # 5. MAC EOS Validates & SHADOW Seals
        # Use ExecutionGuard for atomic action
        result = self.prestige.core.execute_commerce_action(
            "prestige.workflow.luxury_package",
            actor_ctx,
            self._finalize_package,
            best_hotel, pricing, compliance
        )

        return result

    def _handle_no_availability(self):
        # SHADOW event recorded via action_type in execute_commerce_action
        return {
            "status": "no_availability",
            "recovery_required": True,
            "source_attempts": ["Direct Supply", "TBO Holidays", "RateHawk", "Hotelbeds"]
        }

    def _finalize_package(self, hotel, pricing, compliance):
        return {
            "hotel": hotel,
            "pricing": pricing["pricing_breakdown"],
            "compliance": compliance,
            "status": "VALIDATED_AND_SEALED"
        }
