#!/bin/bash
set -e

echo "🚀 BOOTSTRAPPING MNOS SYSTEM (PROD-READY)..."

# Ports
PORT_GATEWAY=8000
PORT_ELEONE=8001
PORT_SHADOW=8002
PORT_EVENTS=8003
PORT_AEGIS=8004
PORT_FCE=8005

# 1. Start Redis
if command -v redis-server >/dev/null 2>&1; then
    echo "✅ Starting REDIS..."
    redis-server --daemonize yes
    sleep 2
    if ! redis-cli ping | grep -q PONG; then
        echo "❌ REDIS FAILED"
        exit 1
    fi
fi

# Cleanup
trap "echo 'Shutting down services...'; kill \$(jobs -p) 2>/dev/null || true" EXIT

# 2. Start Core
echo "Starting MNOS CORE..."
export REDIS_HOST="localhost"
python3 -u core/eleone/api/main.py --port $PORT_ELEONE &
python3 -u core/shadow/api/main.py --port $PORT_SHADOW &
python3 -u core/events/api/main.py --port $PORT_EVENTS &
python3 -u core/aegis/api/main.py --port $PORT_AEGIS &
python3 -u core/fce/api/main.py --port $PORT_FCE &

# 3. Start Interface
echo "Starting MNOS INTERFACES..."
python3 -u interfaces/gateway/api/main.py --port $PORT_GATEWAY &

# 4. Start Modules (Subset for validation)
echo "Starting MNOS MODULES..."
python3 -u modules/lifeline/api/main.py --port 8006 &

# Health Check Helper
check_health() {
    local url=$1
    local name=$2
    echo -n "Waiting for $name... "
    for i in {1..20}; do
        if curl -sf "$url" > /dev/null; then
            echo "✅"
            return 0
        fi
        sleep 1
    done
    echo "❌"
    return 1
}

# 5. Verification
check_health "http://localhost:$PORT_GATEWAY/health" "Gateway" || exit 1
check_health "http://localhost:$PORT_ELEONE/health" "ELEONE" || exit 1
check_health "http://localhost:$PORT_SHADOW/health" "SHADOW" || exit 1
check_health "http://localhost:$PORT_EVENTS/health" "Events" || exit 1
check_health "http://localhost:$PORT_AEGIS/health" "Aegis" || exit 1
check_health "http://localhost:$PORT_FCE/health" "FCE" || exit 1

echo "✅ MNOS SYSTEM FULLY VERIFIED AND RUNNING"
wait
