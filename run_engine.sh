#!/bin/bash
set -euo pipefail

echo "🚀 BOOTSTRAPPING BUILDX SYSTEM..."

# Paths check
PATHS=(
    "services/gateway/main.py"
    "services/gateway/event_worker.py"
    "services/eleone/main.py"
    "services/shadow/main.py"
    "services/svd/main.py"
    "services/sal/main.py"
    "services/bfi/main.py"
    "edge-node/main.py"
)

for path in "${PATHS[@]}"; do
    [ -f "$path" ] || { echo "❌ ERROR: Missing $path"; exit 1; }
done

# Ports
PORT_GATEWAY=8000
PORT_ELEONE=8001
PORT_SHADOW=8002
PORT_SVD=8003
PORT_SAL=8004
PORT_BFI=8005
PORT_EDGE=8006

# Redis Check
if command -v redis-server >/dev/null 2>&1; then
    echo "✅ REDIS: starting..."
    redis-server --daemonize yes || echo "⚠️ REDIS: already running"
    sleep 1
else
    echo "⚠️ REDIS: not found locally"
fi

# Cleanup
trap "kill \$(jobs -p) 2>/dev/null || true" EXIT

# 1. Gateway
echo "Starting Gateway..."
export REDIS_HOST="localhost"
export ELEONE_URL="http://localhost:$PORT_ELEONE"
export SHADOW_URL="http://localhost:$PORT_SHADOW"
export SVD_URL="http://localhost:$PORT_SVD"
export SAL_URL="http://localhost:$PORT_SAL"
export BFI_URL="http://localhost:$PORT_BFI"
export EDGE_URL="http://localhost:$PORT_EDGE"

python3 services/gateway/main.py --port $PORT_GATEWAY > gateway.log 2>&1 &

# Health Check Loop
check_health() {
    local url=$1
    local name=$2
    local retries=10
    local count=0
    until curl -sf "$url" > /dev/null; do
        ((count++))
        if [ $count -gt $retries ]; then
            echo "❌ ERROR: $name failed to start at $url"
            exit 1
        fi
        sleep 1
    done
    echo "✅ $name is UP"
}

check_health "http://localhost:$PORT_GATEWAY/health" "Gateway"

# 2. Worker
if command -v redis-cli >/dev/null 2>&1 && redis-cli ping >/dev/null 2>&1; then
    echo "Starting Worker..."
    python3 services/gateway/event_worker.py > worker.log 2>&1 &
fi

# 3. Microservices
echo "Starting core microservices..."
python3 services/eleone/main.py --port $PORT_ELEONE > eleone.log 2>&1 &
python3 services/shadow/main.py --port $PORT_SHADOW > shadow.log 2>&1 &
python3 services/svd/main.py --port $PORT_SVD > svd.log 2>&1 &
python3 services/sal/main.py --port $PORT_SAL > sal.log 2>&1 &
python3 services/bfi/main.py --port $PORT_BFI > bfi.log 2>&1 &
python3 edge-node/main.py --port $PORT_EDGE > edge.log 2>&1 &

check_health "http://localhost:$PORT_ELEONE/health" "ELEONE"
check_health "http://localhost:$PORT_SHADOW/health" "SHADOW"
check_health "http://localhost:$PORT_SVD/health" "SVD"
check_health "http://localhost:$PORT_SAL/health" "SAL"
check_health "http://localhost:$PORT_BFI/health" "BFI"
check_health "http://localhost:$PORT_EDGE/health" "Edge Node"

echo "✅ BUILDX SYSTEM FULLY VERIFIED"
echo "Gateway: http://localhost:$PORT_GATEWAY"
echo "System Status: http://localhost:$PORT_GATEWAY/system/status"

wait
