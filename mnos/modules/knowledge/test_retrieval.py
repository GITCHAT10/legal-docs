from mnos.modules.knowledge.service import knowledge_core
import re

def test_retrieval():
    print("--- 🧠 KNOWLEDGE CORE RETRIEVAL TEST ---")
    dna = "NEXUS DNA: Bookings are handled by FCE. Arrivals trigger AQUA. Emergencies trigger LIFELINE."
    knowledge_core.ingest("NEXUS_DNA", dna)

    query = "book"
    results = knowledge_core.query(query)

    print(f"Query: '{query}'")
    print(f"Results: {results}")

    # Directive: Replace print statements with Hard Assertions.
    # If SILVIA retrieves incorrect knowledge, the build must BREAK.
    assert results, f"SILVIA: No results found for query '{query}'"
    assert "Bookings" in results[0]["text"], f"SILVIA: Incorrect knowledge retrieved. Expected 'Bookings', got '{results[0]['text']}'"

    print("Result: OK (Assertions Passed)")
    return True

if __name__ == "__main__":
    test_retrieval()
