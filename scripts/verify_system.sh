#!/bin/bash
set -euo pipefail

echo "🔍 VERIFYING BUILDX SYSTEM STATE..."

# Standard Ports
# Core
# 8000: API
# 8001: ELEONE
# 8002: SHADOW
# 8003: Router
# 8004: SAL
# 8006: EdgeNode
# Modules (Simulation ports from run_engine.sh)
# 9001-9007

CORE_PORTS=(8000 8001 8002 8003 8004 8006)
CORE_NAMES=("MNOS-API" "ELEONE" "SHADOW" "Router" "SAL" "EdgeNode")

# 1. Check CORE Health
for i in "${!CORE_PORTS[@]}"; do
    PORT=${CORE_PORTS[$i]}
    NAME=${CORE_NAMES[$i]}
    echo -n "Checking $NAME (Port $PORT)... "
    if curl -sf "http://localhost:$PORT/health" > /dev/null; then
        echo "✅ OK"
    else
        echo "❌ DOWN"
        exit 1
    fi
done

# 2. Confirm Redis Connection
echo -n "Confirming Redis connectivity... "
if command -v redis-cli >/dev/null 2>&1 && redis-cli ping | grep -q PONG; then
    echo "✅ OK"
else
    echo "⚠️ REDIS NOT RESPONDING (Required for full pipeline)"
fi

echo "✅ SYSTEM CORE IS VERIFIED AND RUNNABLE"
