#!/bin/bash
set -euo pipefail

echo "🔍 Validating BUILDX Stack Health..."

PORTS=(8000 8001 8002 8003 8004 8005 8006)
NAMES=("Gateway" "ELEONE" "SHADOW" "SVD" "SAL" "BFI" "EdgeNode")

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

echo "✅ ALL SERVICES ARE HEALTHY"
