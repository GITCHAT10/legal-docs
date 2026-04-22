from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class MarsContext(BaseModel):
    user_id: Optional[str] = None # AEGIS Identity
    location: str
    time: datetime = Field(default_factory=datetime.now)
    system_state: str = "OPTIMAL" # OPTIMAL, DEGRADED, FAIL-STOP
    occupancy: bool = False

class MarsContextEngine:
    """
    MARS CONTEXT ENGINE: Tracks the environment to drive automation.
    """
    def __init__(self, shadow_logger):
        self.contexts: Dict[str, MarsContext] = {}
        self.shadow_logger = shadow_logger

    def update_context(self, location: str, **kwargs):
        if location not in self.contexts:
            self.contexts[location] = MarsContext(location=location)

        context = self.contexts[location]
        for key, value in kwargs.items():
            if hasattr(context, key):
                setattr(context, key, value)

        context.time = datetime.now()

        # Log change to SHADOW
        self.shadow_logger.log("MARS_CONTEXT_UPDATED", {"location": location, "context": context.model_dump()})
        return context

    def get_context(self, location: str) -> MarsContext:
        return self.contexts.get(location, MarsContext(location=location))
