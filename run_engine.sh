#!/bin/bash
set -e

echo "🚀 BOOTSTRAPPING MNOS-BUILDX SYSTEM..."

# Pre-flight checks
REQUIRED_FILES=(
    "services/core/mnos_api/main.py"
    "services/core/mnos_router/main.py"
    "services/core/eleone/main.py"
    "services/core/shadow/main.py"
    "services/core/sal/main.py"
    "services/core/event_worker.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ CRITICAL: Missing $file"
        exit 1
    fi
done

# Ports
PORT_API=8000
PORT_ELEONE=8001
PORT_SHADOW=8002
PORT_ROUTER=8003
PORT_SAL=8004
PORT_SVD=9006
PORT_BFI=9007

# 1. Start Redis
if command -v redis-server >/dev/null 2>&1; then
    echo "✅ Starting REDIS..."
    redis-server --daemonize yes
    sleep 2
    if ! redis-cli ping | grep -q PONG; then
        echo "❌ REDIS FAILED TO START"
        exit 1
    fi
else
    echo "⚠️ REDIS-SERVER NOT FOUND"
fi

# Cleanup
trap "echo 'Stopping services...'; kill \$(jobs -p) 2>/dev/null || true" EXIT

# 2. Start CORE Services
echo "Starting MNOS CORE..."
python3 services/core/eleone/main.py &
python3 services/core/shadow/main.py &
python3 services/core/sal/main.py &
sleep 2

# 3. Start API and Router
echo "Starting MNOS API & Router..."
export REDIS_HOST="localhost"
python3 services/core/mnos_router/main.py --port $PORT_ROUTER &
python3 services/core/mnos_api/main.py --port $PORT_API &
python3 services/core/event_worker.py &

# 4. Start MODULES (simulation)
echo "Starting MNOS MODULES..."
python3 modules/xport/main.py --port 9001 &
python3 modules/aqua/main.py --port 9002 &
python3 modules/inn/main.py --port 9003 &
python3 modules/skygodown/main.py --port 9004 &
python3 modules/atollairways/main.py --port 9005 &
python3 modules/svd/main.py --port $PORT_SVD &
python3 modules/bfi/main.py --port $PORT_BFI &

# 5. Health Verification
check_health() {
    local url=$1
    local name=$2
    echo -n "Checking $name... "
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

check_health "http://localhost:8001/health" "ELEONE" || exit 1
check_health "http://localhost:8002/health" "SHADOW" || exit 1
check_health "http://localhost:8004/health" "SAL" || exit 1
check_health "http://localhost:8000/health" "MNOS-API" || exit 1

echo "✅ MNOS-BUILDX SYSTEM FULLY VERIFIED"
wait
