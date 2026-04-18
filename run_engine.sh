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
    "edge-node/main.py"
)

for path in "${PATHS[@]}"; do
    if [ ! -f "$path" ]; then
        echo "❌ ERROR: Missing required file: $path"
        exit 1
    fi
done

# Ports
PORT_GATEWAY=8000
PORT_ELEONE=8001
PORT_SHADOW=8002
PORT_SVD=8003
PORT_SAL=8004
PORT_BFI=8005
PORT_EDGE=8006

# 1. Redis check and startup
if command -v redis-server >/dev/null 2>&1; then
    echo "✅ REDIS: starting local server..."
    redis-server --daemonize yes || echo "⚠️ REDIS: already running or failed to start"
    # Wait for Redis
    for i in {1..5}; do
        if command -v redis-cli >/dev/null 2>&1 && redis-cli ping >/dev/null 2>&1; then
            echo "✅ REDIS: ready"
            break
        fi
        sleep 1
    done
else
    echo "⚠️ REDIS: not available locally, event worker may fail"
fi

# Cleanup on exit
trap "kill \$(jobs -p) 2>/dev/null || true" EXIT

# 2. Start Gateway
echo "Starting Gateway..."
export ELEONE_URL="http://localhost:$PORT_ELEONE"
export SHADOW_URL="http://localhost:$PORT_SHADOW"
export SVD_URL="http://localhost:$PORT_SVD"
export SAL_URL="http://localhost:$PORT_SAL"
export BFI_URL="http://localhost:$PORT_BFI"
export REDIS_HOST="localhost"

python3 services/gateway/main.py --port $PORT_GATEWAY > /dev/null 2>&1 &
sleep 2
curl -sf "http://localhost:$PORT_GATEWAY/health" > /dev/null || { echo "❌ ERROR: Gateway failed health check"; exit 1; }

# 3. Start Event Worker
if command -v redis-cli >/dev/null 2>&1 && redis-cli ping >/dev/null 2>&1; then
    echo "✅ Starting event worker..."
    python3 services/gateway/event_worker.py > /dev/null 2>&1 &
else
    echo "⚠️ Skipping event worker (Redis not ready)"
fi

# 4. Start Other services
echo "Starting core services..."
python3 services/eleone/main.py --port $PORT_ELEONE > /dev/null 2>&1 &
python3 services/shadow/main.py --port $PORT_SHADOW > /dev/null 2>&1 &
python3 services/svd/main.py --port $PORT_SVD > /dev/null 2>&1 &
python3 services/sal/main.py --port $PORT_SAL > /dev/null 2>&1 &
python3 services/bfi/main.py --port $PORT_BFI > /dev/null 2>&1 &
python3 edge-node/main.py --port $PORT_EDGE > /dev/null 2>&1 &

# Wait for all services
sleep 5

# Verify health of ALL services
SERVICES_TO_CHECK=(
    "http://localhost:$PORT_ELEONE/health"
    "http://localhost:$PORT_SHADOW/health"
    "http://localhost:$PORT_SVD/health"
    "http://localhost:$PORT_SAL/health"
    "http://localhost:$PORT_BFI/health"
    "http://localhost:$PORT_EDGE/health"
)

for url in "${SERVICES_TO_CHECK[@]}"; do
    echo "Checking $url..."
    curl -sf "$url" > /dev/null || { echo "❌ ERROR: Service at $url failed health check"; exit 1; }
done

echo "✅ BUILDX SYSTEM IS UP AND VERIFIED"
echo "GATEWAY: http://localhost:$PORT_GATEWAY"

wait
