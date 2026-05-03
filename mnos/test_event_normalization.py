import sys
import os

# Ensure mnos is in path
sys.path.append(os.getcwd())

from mnos.interfaces.sky_i.comms.whatsapp import whatsapp

def test_event_normalization():
    print("[RC-GATE] Testing Event Normalization...")

    # 1. Test elegal.* (should not be prefixed)
    elegal_intent = "elegal.pulse.processed"
    normalized = whatsapp.normalize_event_type(elegal_intent)
    print(f" -> {elegal_intent} -> {normalized}")
    assert normalized == elegal_intent

    # 2. Test legal.* (should not be prefixed)
    legal_intent = "legal.matter.created"
    normalized = whatsapp.normalize_event_type(legal_intent)
    print(f" -> {legal_intent} -> {normalized}")
    assert normalized == legal_intent

    # 3. Test nexus.* (should not be prefixed)
    nexus_intent = "nexus.booking.created"
    normalized = whatsapp.normalize_event_type(nexus_intent)
    print(f" -> {nexus_intent} -> {normalized}")
    assert normalized == nexus_intent

    # 4. Test fce.* (should not be prefixed)
    fce_intent = "fce.payment.processed"
    normalized = whatsapp.normalize_event_type(fce_intent)
    print(f" -> {fce_intent} -> {normalized}")
    assert normalized == fce_intent

    # 5. Test bare intent (should be prefixed with nexus.)
    bare_intent = "guest_arrival"
    normalized = whatsapp.normalize_event_type(bare_intent)
    print(f" -> {bare_intent} -> {normalized}")
    assert normalized == "nexus.guest_arrival"

    print(" -> PASSED: Event normalization verified.")

if __name__ == "__main__":
    test_event_normalization()
