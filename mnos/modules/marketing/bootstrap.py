from mnos.api.marketing import create_marketing_router
from mnos.modules.marketing.engine import SovereignMarketingEngine


def mount_sovereign_marketing(app, core, get_actor_ctx, prefix: str = "/imoxon"):
    """Mount the MIG Sovereign Marketing module on the consolidated FastAPI app."""
    engine = SovereignMarketingEngine(core)
    app.include_router(create_marketing_router(engine, get_actor_ctx), prefix=prefix)
    return engine
