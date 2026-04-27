#!/bin/bash
# scripts/deploy_gate.sh — PATCH v1.1

set -euo pipefail

echo "🔐 Running MAC EOS Pre-Merge Integrity Gates..."

# Gate 1: Orchestrator fake-order test
echo "✅ Gate 1: Fake order rejection"
python -m pytest tests/test_mac_eos_integrity.py::test_fake_order_rejected -v
if [ $? -ne 0 ]; then
  echo "❌ Gate 1 FAILED: Orchestrator allows fake confirmations"
  exit 1
fi

# Gate 2: Auth compatibility test
echo "✅ Gate 2: Session auth compatibility"
python -m pytest tests/test_mac_eos_integrity.py::test_session_auth_allowed_on_dual_paths -v
if [ $? -ne 0 ]; then
  echo "❌ Gate 2 FAILED: Session auth broken on dual-auth paths"
  exit 1
fi

# Gate 3: Strict path enforcement
echo "✅ Gate 3: Strict path auth enforcement"
python -m pytest tests/test_mac_eos_integrity.py::test_strict_path_rejects_session_auth -v
if [ $? -ne 0 ]; then
  echo "❌ Gate 3 FAILED: Strict paths accept weak auth"
  exit 1
fi

# Gate 4: System invariant test
echo "✅ Gate 4: Invariant no confirm without order"
python -m pytest tests/test_mac_eos_integrity.py::test_invariant_no_confirm_without_order -v
if [ $? -ne 0 ]; then
  echo "❌ Gate 4 FAILED: System invariant violated"
  exit 1
fi

# Gate 5: SHADOW ledger integrity check
echo "✅ Gate 5: SHADOW ledger genesis validation"
python scripts/shadow_genesis.py --verify
if [ $? -ne 0 ]; then
  echo "❌ Gate 5 FAILED: SHADOW ledger integrity check failed"
  exit 1
fi

echo "🟢 All integrity gates passed. Merge approved."
exit 0
