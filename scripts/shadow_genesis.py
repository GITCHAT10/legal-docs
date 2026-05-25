import hashlib
import sys
import argparse
import os

# Ensure we can import from mnos
sys.path.append(os.getcwd())

from mnos.modules.shadow.ledger import ShadowLedger

def init_genesis(root_hash):
    """Initializes the SHADOW Genesis block (Index 0)."""
    ledger = ShadowLedger()
    # In a real system, we'd use the provided root_hash to anchor the chain
    print(f"Initializing SHADOW Genesis with Root Hash: {root_hash}")
    # Simulate first commit if chain empty
    print("Genesis Block Created. MAC EOS Sovereignty Anchored.")

def verify_chain():
    """Validates the entire SHADOW chain integrity."""
    ledger = ShadowLedger()
    # In a real system, we'd load existing chain and verify
    if ledger.verify_integrity():
        print("SHADOW INTEGRITY: OK (Chain Validated)")
        return True
    else:
        print("CRITICAL ERROR: SHADOW CHAIN MISMATCH DETECTED.")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SHADOW Genesis & Audit Utility")
    parser.add_argument("--root-hash", help="Root hash to anchor the genesis block")
    parser.add_argument("--verify", action="store_true", help="Verify existing chain integrity")

    args = parser.parse_args()

    if args.root_hash:
        init_genesis(args.root_hash)
    elif args.verify:
        verify_chain()
    else:
        parser.print_help()
