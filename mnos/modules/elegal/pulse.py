from typing import Dict, Any, List
from mnos.core.ai.silvia import silvia
from mnos.modules.knowledge.service import knowledge_core
from mnos.modules.shadow.service import shadow

class LegalPulse:
    """
    eLEGAL Pulse (The J4/J5 Hub): AI communication layer for multi-brand legal interface.
    Manages legal queries for Sala Hotels, 97 Degrees East, etc.
    """
    BRANDS = [
        "Sala Hotels", "97 Degrees East", "fushigili", "Velaagili",
        "Per Aquam", "V1", "V3", "V4"
    ]

    def process_legal_query(self, brand: str, query: str) -> Dict[str, Any]:
        """
        Processes a legal query through SILVIA and Knowledge Core.
        """
        if brand not in self.BRANDS:
            return {"status": "ERROR", "message": f"Brand {brand} not recognized by eLEGAL Pulse."}

        # Contextualize query with brand DNA
        contextual_query = f"[{brand}] Legal Inquiry: {query}"

        # Route through SILVIA
        response = silvia.process_request(contextual_query)

        # Commit interaction to SHADOW
        shadow.commit("elegal.pulse.processed", {
            "brand": brand,
            "query": query,
            "silvia_response": response
        })

        return response

elegal_pulse = LegalPulse()
