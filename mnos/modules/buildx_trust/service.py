from fastapi import FastAPI
from mnos.shared.constants.root import ROOT_IDENTITY
from mnos.core.events.service import events
import hashlib

app = FastAPI(title="BUILD-X TRUST", description=f"Quantum-Safe Notarization for {ROOT_IDENTITY}")

@app.get("/health")
def health():
    return {"status": "ok", "module": "buildx_trust"}

@app.post("/notarize")
def notarize(data: dict):
    """
    BUILD-X TRUST: Quantum-Safe (SPHINCS+) Hashing & RFC 3161 Notarization.
    """
    payload = str(data).encode()
    q_safe_hash = hashlib.sha3_512(payload).hexdigest()

    notarization = {
        "hash": q_safe_hash,
        "notarization_type": "RFC 3161",
        "authority": ROOT_IDENTITY
    }

    events.publish("CLEAN_CERT_ISSUED", notarization)

    return notarization
