import json
import hashlib
from datetime import datetime, timezone
from mnos.config import config
from mnos.modules.aig_shadow.service import aig_shadow

def generate_merkle_witness_bundle(bond_id: str):
    """
    Exports cryptographic proof for a specific system state.
    Witness for MIG_PUBLIC_TRANSPARENCY_GATES.
    """
    print(f"--- 📜 EXPORTING SOVEREIGN PROOF: {bond_id} ---")

    # 1. State Capture
    state = {
        "bond_id": bond_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ledger_size": len(aig_shadow.chain),
        "merkle_root": aig_shadow.chain[-1]["hash"] if aig_shadow.chain else None,
        "integrity_verified": aig_shadow.verify_integrity(start_index=0)
    }

    # 2. Cryptographic Signature
    witness_hash = hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()

    bundle = {
        "witness": state,
        "signature": witness_hash,
        "gate": "MIG_PUBLIC_TRANSPARENCY_GATES",
        "status": "SEALED"
    }

    output_path = f"mnos/docs/witness_{bond_id}.json"
    with open(output_path, "w") as f:
        json.dump(bundle, f, indent=2)

    print(f"Proof exported to: {output_path}")
    return bundle

if __name__ == "__main__":
    generate_merkle_witness_bundle("MIG-CLOUD-GENESIS-2026")
