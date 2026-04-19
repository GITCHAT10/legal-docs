#!/bin/bash
set -euo pipefail

echo "🔍 VERIFYING BUILDX SYSTEM STATE..."

# Standard Ports
PORTS=(8000 8001 8002 8003 8004 8005 8006)
NAMES=("Gateway" "ELEONE" "SHADOW" "SVD" "SAL" "BFI" "EdgeNode")

# 1. Check HTTP Health Endpoints
for i in "${!PORTS[@]}"; do
    PORT=${PORTS[$i]}
    NAME=${NAMES[$i]}
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
    echo "❌ FAILED"
    exit 1
fi

echo "✅ SYSTEM IS TRULY RUNNING AND HEALTHY"
