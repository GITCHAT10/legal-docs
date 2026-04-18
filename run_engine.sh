#!/bin/bash
set -e

echo "🚀 BOOTSTRAPPING BUILDX HARDENED SYSTEM..."

# Check dependencies
command -v python3 >/dev/null 2>&1 || { echo >&2 "Python3 required. Aborting."; exit 1; }

# Start services on unique ports for local simulation
echo "Starting services..."
PORT_ELEONE=8001
PORT_SHADOW=8002
PORT_SVD=8003
PORT_SAL=8004
PORT_BFI=8005
PORT_GATEWAY=8000
PORT_EDGE=8006

python3 services/eleone/main.py --port $PORT_ELEONE > /dev/null 2>&1 &
python3 services/shadow/main.py --port $PORT_SHADOW > /dev/null 2>&1 &
python3 services/svd/main.py --port $PORT_SVD > /dev/null 2>&1 &
python3 services/sal/main.py --port $PORT_SAL > /dev/null 2>&1 &
python3 services/bfi/main.py --port $PORT_BFI > /dev/null 2>&1 &

# Gateway setup
export ELEONE_URL="http://localhost:$PORT_ELEONE"
export SHADOW_URL="http://localhost:$PORT_SHADOW"
export SVD_URL="http://localhost:$PORT_SVD"
export SAL_URL="http://localhost:$PORT_SAL"
export BFI_URL="http://localhost:$PORT_BFI"
export REDIS_HOST="localhost"

python3 services/gateway/main.py --port $PORT_GATEWAY > /dev/null 2>&1 &
python3 services/gateway/event_worker.py > /dev/null 2>&1 &
python3 edge-node/main.py --port $PORT_EDGE > /dev/null 2>&1 &

sleep 5

echo "Hardened system services are up."
echo "GATEWAY (MNOS Integrated): http://localhost:$PORT_GATEWAY"
echo "EVENT PIPELINE: Listening on Redis"

# Kill background processes on exit
trap "kill $(jobs -p)" EXIT

wait
