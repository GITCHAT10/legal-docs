#!/bin/bash
set -e

echo "🚀 BOOTSTRAPPING BUILDX SYSTEM (HARD EXECUTION MODE)..."

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
    echo "✅ Starting REDIS server..."
    redis-server --daemonize yes

    # Block until Redis is ready
    READY=0
    for i in {1..10}; do
        if redis-cli ping | grep -q PONG; then
            READY=1
            echo "✅ REDIS is UP"
            break
        fi
        sleep 1
    done
    if [ $READY -eq 0 ]; then
        echo "❌ ERROR: Redis failed to respond"
        exit 1
    fi
else
    echo "❌ ERROR: redis-server not found"
    exit 1
fi

# Cleanup on exit
trap "echo 'Stopping services...'; kill \$(jobs -p) 2>/dev/null || true" EXIT

# 2. Start Services
echo "Starting Services (No logs suppressed)..."

export PORT=$PORT_GATEWAY
python3 services/gateway/main.py &

export PORT=$PORT_ELEONE
python3 services/eleone/main.py &

export PORT=$PORT_SHADOW
python3 services/shadow/main.py &

export PORT=$PORT_SVD
python3 services/svd/main.py &

export PORT=$PORT_SAL
python3 services/sal/main.py &

export PORT=$PORT_BFI
python3 services/bfi/main.py &

export PORT=$PORT_EDGE
python3 edge-node/main.py &

# 3. Health Checks
check_health() {
    local url=$1
    local name=$2
    echo -n "Waiting for $name at $url... "
    for i in {1..20}; do
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
check_health "http://localhost:$PORT_ELEONE/health" "ELEONE" || exit 1
check_health "http://localhost:$PORT_SHADOW/health" "SHADOW" || exit 1
check_health "http://localhost:$PORT_SVD/health" "SVD" || exit 1
check_health "http://localhost:$PORT_SAL/health" "SAL" || exit 1
check_health "http://localhost:$PORT_BFI/health" "BFI" || exit 1
check_health "http://localhost:$PORT_EDGE/health" "Edge Node" || exit 1

echo "✅ BUILDX SYSTEM IS FULLY OPERATIONAL"
wait
