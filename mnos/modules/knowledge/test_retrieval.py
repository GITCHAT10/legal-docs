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
    if results and "Bookings" in results[0]["text"]:
        print("Result: OK")
        return True
    else:
        print("Result: FAILED")
        return False

if __name__ == "__main__":
    test_retrieval()
