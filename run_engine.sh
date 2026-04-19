#!/bin/bash
set -e

echo "🚀 BOOTSTRAPPING BUILDX SYSTEM (EXECUTION FIX MODE)..."

# Ports
PORT_GATEWAY=8000
PORT_ELEONE=8001
PORT_SHADOW=8002
PORT_SVD=8003
PORT_SAL=8004
PORT_BFI=8005
PORT_EDGE=8006

# 1. Redis Initialization
if command -v redis-server >/dev/null 2>&1; then
    echo "✅ REDIS: starting..."
    redis-server --daemonize yes || echo "⚠️ REDIS: already running"

    # Verify Redis is actually running
    READY=0
    for i in {1..5}; do
        if redis-cli ping | grep -q PONG; then
            READY=1
            echo "✅ REDIS: connected"
            break
        fi
        sleep 1
    done
    if [ $READY -eq 0 ]; then
        echo "❌ ERROR: Redis failed to start"
        exit 1
    fi
else
    echo "❌ ERROR: redis-server not found. Redis is mandatory."
    exit 1
fi

# Cleanup on exit
trap "echo 'Cleaning up processes...'; kill \$(jobs -p) 2>/dev/null || true" EXIT

# 2. Start Gateway
echo "Starting Gateway..."
export REDIS_HOST="localhost"
export ELEONE_URL="http://localhost:$PORT_ELEONE"
export SHADOW_URL="http://localhost:$PORT_SHADOW"
export SVD_URL="http://localhost:$PORT_SVD"
export SAL_URL="http://localhost:$PORT_SAL"
export BFI_URL="http://localhost:$PORT_BFI"
export EDGE_URL="http://localhost:$PORT_EDGE"

python3 services/gateway/main.py --port $PORT_GATEWAY &
sleep 2

# Health check helper
check_health() {
    local url=$1
    local name=$2
    echo "Verifying $name at $url..."
    curl -sf "$url" > /dev/null || { echo "❌ ERROR: $name failed to start"; exit 1; }
    echo "✅ $name is UP"
}

check_health "http://localhost:$PORT_GATEWAY/health" "Gateway"

# 3. Start Event Worker
echo "Starting Event Worker..."
python3 services/gateway/event_worker.py &

# 4. Start Core Microservices
echo "Starting core microservices..."
python3 services/eleone/main.py --port $PORT_ELEONE &
python3 services/shadow/main.py --port $PORT_SHADOW &
python3 services/svd/main.py --port $PORT_SVD &
python3 services/sal/main.py --port $PORT_SAL &
python3 services/bfi/main.py --port $PORT_BFI &
python3 edge-node/main.py --port $PORT_EDGE &

sleep 5

# Final Health Verification
check_health "http://localhost:$PORT_ELEONE/health" "ELEONE"
check_health "http://localhost:$PORT_SHADOW/health" "SHADOW"
check_health "http://localhost:$PORT_SVD/health" "SVD"
check_health "http://localhost:$PORT_SAL/health" "SAL"
check_health "http://localhost:$PORT_BFI/health" "BFI"
check_health "http://localhost:$PORT_EDGE/health" "Edge Node"

echo "✅ BUILDX SYSTEM IS RUNNING END-TO-END"
echo "Gateway: http://localhost:$PORT_GATEWAY"
echo "System Status: http://localhost:$PORT_GATEWAY/system/status"

wait
