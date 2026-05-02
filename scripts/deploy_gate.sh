#!/bin/bash
# scripts/deploy_gate.sh — PATCH v1.3

set -euo pipefail

echo "🔐 Running MAC EOS Pre-Merge Integrity Gates..."

# Gate 1: Orchestrator fake-order test
echo "✅ Gate 1: Fake order rejection"
python -m pytest tests/test_mac_eos_integrity.py::test_confirm_real_world_fails_for_unknown_order -v

# Gate 2: Auth compatibility test
echo "✅ Gate 2: Session auth compatibility"
python -m pytest tests/test_mac_eos_integrity.py::test_session_auth_allowed_on_user_paths -v

# Gate 3: Strict path enforcement
echo "✅ Gate 3: Strict path auth enforcement"
python -m pytest tests/test_mac_eos_integrity.py::test_strict_path_rejects_session_only -v

# Gate 4: System invariant test
echo "✅ Gate 4: Success path validation"
python -m pytest tests/test_mac_eos_integrity.py::test_confirm_real_world_success_path -v

# Gate 5: SHADOW ledger integrity check
echo "✅ Gate 5: SHADOW ledger genesis validation"
python scripts/shadow_genesis.py --verify

echo "🟢 All integrity gates passed. Merge approved."
