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

# 1. Redis
if command -v redis-server >/dev/null 2>&1; then
    echo "✅ REDIS: starting..."
    redis-server --daemonize yes || echo "⚠️ REDIS: already running"
    sleep 1
else
    echo "⚠️ REDIS: not found locally"
fi

# Cleanup
trap "kill \$(jobs -p) 2>/dev/null || true" EXIT

# 2. Gateway
echo "Starting Gateway..."
export REDIS_HOST="localhost"
export ELEONE_URL="http://localhost:$PORT_ELEONE"
export SHADOW_URL="http://localhost:$PORT_SHADOW"
export SVD_URL="http://localhost:$PORT_SVD"
export SAL_URL="http://localhost:$PORT_SAL"
export BFI_URL="http://localhost:$PORT_BFI"
export EDGE_URL="http://localhost:$PORT_EDGE"

python3 services/gateway/main.py --port $PORT_GATEWAY > gateway.log 2>&1 &
sleep 2
curl -sf "http://localhost:$PORT_GATEWAY/health" > /dev/null || { echo "❌ ERROR: Gateway failed"; exit 1; }

# 3. Worker
if command -v redis-cli >/dev/null 2>&1 && redis-cli ping >/dev/null 2>&1; then
    echo "✅ Starting Worker..."
    python3 services/gateway/event_worker.py > worker.log 2>&1 &
else
    echo "⚠️ Skipping Worker (Redis not ready)"
fi

# 4. Other services
echo "Starting microservices..."
python3 services/eleone/main.py --port $PORT_ELEONE > /dev/null 2>&1 &
python3 services/shadow/main.py --port $PORT_SHADOW > /dev/null 2>&1 &
python3 services/svd/main.py --port $PORT_SVD > /dev/null 2>&1 &
python3 services/sal/main.py --port $PORT_SAL > /dev/null 2>&1 &
python3 services/bfi/main.py --port $PORT_BFI > /dev/null 2>&1 &
python3 edge-node/main.py --port $PORT_EDGE > /dev/null 2>&1 &

sleep 5

# Health checks
CHECK_URLS=(
    "http://localhost:$PORT_ELEONE/health"
    "http://localhost:$PORT_SHADOW/health"
    "http://localhost:$PORT_SVD/health"
    "http://localhost:$PORT_SAL/health"
    "http://localhost:$PORT_BFI/health"
    "http://localhost:$PORT_EDGE/health"
)

for url in "${CHECK_URLS[@]}"; do
    curl -sf "$url" > /dev/null || { echo "❌ ERROR: Service at $url failed health check"; exit 1; }
done

echo "✅ BUILDX SYSTEM IS FULLY UP"
echo "Gateway: http://localhost:8000"
echo "System Status: http://localhost:8000/system/status"

wait
