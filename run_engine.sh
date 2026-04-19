#!/bin/bash
# run_engine.sh

echo "🚀 INITIALIZING SKYFARM ENGINE..."

# Clean old state
rm -f skyfarm.db mnos.db mnos.log skyfarm.log

# Set production env vars from environment or fallback
export SKYFARM_INTEGRATION_SECRET="${SKYFARM_INTEGRATION_SECRET:-dev_fallback_secret}"
export MNOS_INTEGRATION_SECRET="${MNOS_INTEGRATION_SECRET:-dev_fallback_secret}"
export NEXGEN_SECRET="${NEXGEN_SECRET:-dev_fallback_secret}"

# Configure PATENTE_HASH for tests
# Hash of 'dev_fallback_token'
export PATENTE_HASH="5063ad7329d8724779e8003cccabf7aad2220b58c804375dc3e968bdc811587c"
export SKYFARM_ENV="prod"
export MNOS_ENV="prod"

echo "📡 STARTING MNOS GATEWAY..."
uvicorn mnos.main:app --host 0.0.0.0 --port 8000 > mnos.log 2>&1 &
MNOS_PID=$!

echo "⚙️ STARTING MNOS EVENT WORKER..."
PYTHONPATH=$PYTHONPATH:. python3 -u mnos/worker.py > mnos_worker.log 2>&1 &
WORKER_PID=$!

echo "🔌 STARTING EDGE NODE FUEL CONTROLLER..."
PYTHONPATH=$PYTHONPATH:. python3 -u edge-node/fuel_controller.py > edge_node.log 2>&1 &
EDGE_PID=$!

echo "🚜 STARTING SKYFARM SYSTEM..."
uvicorn skyfarm.main:app --host 0.0.0.0 --port 8001 > skyfarm.log 2>&1 &
SKYFARM_PID=$!

echo "🏗️ STARTING UNIFIED AIRPORT & PORT SUITE..."
uvicorn unified_suite.main:app --host 0.0.0.0 --port 8003 > unified_suite.log 2>&1 &
UNIFIED_PID=$!

# Wait for startup
echo "⏳ WAITING FOR SERVICES TO BOOT..."
sleep 10

# Run Operating Loop Simulation
echo "🔄 EXECUTING FULL OPERATING LOOP..."
python3 simulate_full_operating_loop.py

# Run Fuel System Test
echo "⛽ EXECUTING FUEL AUTHORIZATION CONTROL SYSTEM TEST..."
python3 test_fuel_flow.py

# Run Unified Suite Simulation
echo "🛫 EXECUTING UNIFIED AIRPORT & PORT SUITE SIMULATION..."
python3 simulate_unified_suite.py

# Final Verification
echo "🔍 VERIFYING PERSISTENT STATE..."
echo "--- MNOS WORKER LOG ---"
cat mnos_worker.log
echo "--- EDGE NODE LOG ---"
cat edge_node.log
echo "--- SKYFARM OUTBOX ---"
sqlite3 skyfarm.db "SELECT event_type, status FROM integration_outbox;"
echo "--- MNOS EVENT LOG ---"
sqlite3 mnos.db "SELECT id, status FROM event_ingest_log;"
echo "--- MNOS SHADOW LEDGER ---"
sqlite3 mnos.db "SELECT event_type, previous_hash, current_hash FROM shadow_ledger;"

# Cleanup
echo "🛑 SHUTTING DOWN SERVICES..."
kill $MNOS_PID $SKYFARM_PID $WORKER_PID $EDGE_PID $UNIFIED_PID
echo "✅ ENGINE RUN COMPLETED."
