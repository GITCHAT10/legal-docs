from mnos.modules.knowledge.service import knowledge_core
import re

def test_retrieval():
    """Knowledge Core Retrieval Test (P2 Assertion Fix)."""
    print("--- 🧠 KNOWLEDGE CORE RETRIEVAL TEST ---")
    dna = "NEXUS DNA: Bookings are handled by FCE. Arrivals trigger AQUA. Emergencies trigger LIFELINE."
    knowledge_core.ingest("NEXUS_DNA", dna)

    query = "book"
    results = knowledge_core.query(query)

    print(f"Query: '{query}'")
    print(f"Results: {results}")

    # Enforce hard assert statements exclusively
    assert results is not None, "Retrieval Error: Results object is None"
    assert len(results) > 0, f"Retrieval Error: No results found for query '{query}'"
    assert "Bookings" in results[0]["text"], f"Retrieval DNA Mismatch: Expected 'Bookings' in {results[0]['text']}"

    print("Result: OK")

if __name__ == "__main__":
    test_retrieval()
