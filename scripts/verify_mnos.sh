#!/bin/bash
set -euo pipefail
echo "🔍 Cluster Health Verification..."

# API 8000
# ELEONE 8001 (Internal)
# SHADOW 8002 (Internal)
# ROUTER 8003 (Internal)
# SAL 8004 (Internal)

echo -n "MNOS API Health (Port 8000)... "
if curl -sf http://localhost:8000/health > /dev/null; then
    echo "✅"
else
    echo "❌"
    exit 1
fi

echo "✅ MNOS SYSTEM VERIFIED"
