#!/bin/bash
set -euo pipefail

echo "🚀 BOOTSTRAPPING BUILDX SYSTEM..."

# Check required paths
PATHS=(
    "services/gateway/main.py"
    "services/eleone/main.py"
    "services/shadow/main.py"
    "services/svd/main.py"
    "services/sal/main.py"
    "services/bfi/main.py"
)

for path in "${PATHS[@]}"; do
    if [ ! -f "$path" ]; then
        echo "❌ ERROR: Missing required file: $path"
        exit 1
    fi
done

# Check Edge Node
if [ -f "edge-node/main.py" ]; then
    echo "✅ EDGE NODE: found"
    EDGE_PRESENT=true
else
    echo "⚠️ EDGE NODE: not present, skipping"
    EDGE_PRESENT=false
fi

# Ports
PORT_GATEWAY=8000
PORT_ELEONE=8001
PORT_SHADOW=8002
PORT_SVD=8003
PORT_SAL=8004
PORT_BFI=8005
PORT_EDGE=8006

# Redis check
if command -v redis-server >/dev/null 2>&1; then
    echo "✅ REDIS: starting local server..."
    redis-server --daemonize yes || echo "⚠️ REDIS: already running or failed to start"
else
    echo "⚠️ REDIS: not available locally, event worker may fail"
fi

# Cleanup on exit
trap "kill \$(jobs -p) 2>/dev/null || true" EXIT

echo "Starting services..."
python3 services/eleone/main.py --port $PORT_ELEONE > /dev/null 2>&1 &
python3 services/shadow/main.py --port $PORT_SHADOW > /dev/null 2>&1 &
python3 services/svd/main.py --port $PORT_SVD > /dev/null 2>&1 &
python3 services/sal/main.py --port $PORT_SAL > /dev/null 2>&1 &
python3 services/bfi/main.py --port $PORT_BFI > /dev/null 2>&1 &

if [ "$EDGE_PRESENT" = true ]; then
    python3 edge-node/main.py --port $PORT_EDGE > /dev/null 2>&1 &
fi

# Wait for core services
sleep 5

# Verify health before gateway
SERVICES_TO_CHECK=(
    "http://localhost:$PORT_ELEONE/health"
    "http://localhost:$PORT_SHADOW/health"
    "http://localhost:$PORT_SVD/health"
    "http://localhost:$PORT_SAL/health"
    "http://localhost:$PORT_BFI/health"
)

for url in "${SERVICES_TO_CHECK[@]}"; do
    echo "Checking $url..."
    curl -sf "$url" > /dev/null || { echo "❌ ERROR: Service at $url failed health check"; exit 1; }
done

# Gateway
export ELEONE_URL="http://localhost:$PORT_ELEONE"
export SHADOW_URL="http://localhost:$PORT_SHADOW"
export SVD_URL="http://localhost:$PORT_SVD"
export SAL_URL="http://localhost:$PORT_SAL"
export BFI_URL="http://localhost:$PORT_BFI"

python3 services/gateway/main.py --port $PORT_GATEWAY > /dev/null 2>&1 &
sleep 2
curl -sf "http://localhost:$PORT_GATEWAY/health" > /dev/null || { echo "❌ ERROR: Gateway failed health check"; exit 1; }

# Event worker
if command -v redis-cli >/dev/null 2>&1 && redis-cli ping >/dev/null 2>&1; then
    echo "✅ Starting event worker..."
    python3 services/gateway/event_worker.py > /dev/null 2>&1 &
else
    echo "⚠️ Skipping event worker (Redis not ready)"
fi

echo "✅ BUILDX SYSTEM IS UP"
echo "GATEWAY: http://localhost:$PORT_GATEWAY"

wait
