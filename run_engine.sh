#!/bin/bash
set -e

echo "🚀 BOOTSTRAPPING BUILDX SYSTEM (PRODUCTION ENGINE)..."

# Ports
PORT_GATEWAY=8000
PORT_ELEONE=8001
PORT_SHADOW=8002
PORT_SVD=8003
PORT_SAL=8004
PORT_BFI=8005
PORT_EDGE=8006

# 1. Start Redis
if command -v redis-server >/dev/null 2>&1; then
    echo "✅ REDIS: starting server..."
    redis-server --daemonize yes

    # Verify Redis is actually running
    READY=0
    for i in {1..10}; do
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
    echo "❌ ERROR: redis-server not found"
    exit 1
fi

# Cleanup on exit
trap "echo 'Finalizing processes...'; kill \$(jobs -p) 2>/dev/null || true" EXIT

# 2. Start Gateway
echo "Starting Gateway..."
export REDIS_HOST="localhost"
export GATEWAY_SECRET="mnos-production-secret"
export ELEONE_URL="http://localhost:$PORT_ELEONE"
export SHADOW_URL="http://localhost:$PORT_SHADOW"
export SVD_URL="http://localhost:$PORT_SVD"
export SAL_URL="http://localhost:$PORT_SAL"
export BFI_URL="http://localhost:$PORT_BFI"
export EDGE_URL="http://localhost:$PORT_EDGE"

python3 services/gateway/main.py --port $PORT_GATEWAY &

# 3. Health check helper
check_health() {
    local url=$1
    local name=$2
    echo -n "Waiting for $name... "
    for i in {1..15}; do
        if curl -sf "$url" > /dev/null; then
            echo "✅ UP"
            return 0
        fi
        sleep 1
    done
    echo "❌ FAILED"
    return 1
}

check_health "http://localhost:$PORT_GATEWAY/health" "Gateway" || exit 1

# 4. Start Event Worker
echo "Starting Event Worker..."
python3 services/gateway/event_worker.py &

# 5. Start Core Microservices
echo "Starting core services..."
python3 services/eleone/main.py --port $PORT_ELEONE &
python3 services/shadow/main.py --port $PORT_SHADOW &
python3 services/svd/main.py --port $PORT_SVD &
python3 services/sal/main.py --port $PORT_SAL &
python3 services/bfi/main.py --port $PORT_BFI &
python3 edge-node/main.py --port $PORT_EDGE &

# 6. Final Cluster Verification
check_health "http://localhost:$PORT_ELEONE/health" "ELEONE" || exit 1
check_health "http://localhost:$PORT_SHADOW/health" "SHADOW" || exit 1
check_health "http://localhost:$PORT_SVD/health" "SVD" || exit 1
check_health "http://localhost:$PORT_SAL/health" "SAL" || exit 1
check_health "http://localhost:$PORT_BFI/health" "BFI" || exit 1
check_health "http://localhost:$PORT_EDGE/health" "Edge Node" || exit 1

echo "✅ BUILDX SYSTEM IS FULLY OPERATIONAL"
echo "Gateway: http://localhost:$PORT_GATEWAY"
echo "System Status: http://localhost:$PORT_GATEWAY/system/status"

wait
