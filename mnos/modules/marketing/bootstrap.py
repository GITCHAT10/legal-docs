from mnos.api.marketing import create_marketing_router
from mnos.modules.marketing.anthropic_router import AnthropicModelPolicy
from mnos.modules.marketing.engine import SovereignMarketingEngine
from mnos.modules.marketing.operational_security import MarketingOperationalSecurity


def mount_sovereign_marketing(app, core, get_actor_ctx, prefix: str = "/imoxon"):
    """Mount the MIG Sovereign Marketing module on the consolidated FastAPI app."""
    engine = SovereignMarketingEngine(core)
    engine.ai_model_policy = AnthropicModelPolicy()
    engine.operational_security = MarketingOperationalSecurity()
    app.include_router(create_marketing_router(engine, get_actor_ctx), prefix=prefix)
    return engine
