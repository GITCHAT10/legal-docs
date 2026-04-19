#!/bin/bash
set -euo pipefail
echo "🔍 VERIFYING MNOS-LIFELINE SYSTEM..."

# Standard Ports
# 8000: Gateway
# 8001: ELEONE
# 8002: SHADOW
# 8003: Events
# 8004: Aegis
# 8005: FCE
# 8006: Lifeline

PORTS=(8000 8001 8002 8003 8004 8005 8006)
NAMES=("Gateway" "ELEONE" "SHADOW" "Events" "Aegis" "FCE" "Lifeline")

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

echo "✅ SYSTEM IS TRULY RUNNING AND HEALTHY"
