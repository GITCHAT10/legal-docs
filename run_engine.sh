#!/bin/bash
# run_engine.sh

echo "🚀 INITIALIZING SKYFARM ENGINE..."

# Clean old state
rm -f skyfarm.db mnos.db mnos.log skyfarm.log

# Set production env vars
export SKYFARM_INTEGRATION_SECRET="production_ready_secret"
export MNOS_INTEGRATION_SECRET="production_ready_secret"
export SKYFARM_ENV="prod"
export MNOS_ENV="prod"

echo "📡 STARTING MNOS GATEWAY..."
uvicorn mnos.main:app --host 0.0.0.0 --port 8000 > mnos.log 2>&1 &
MNOS_PID=$!

echo "🚜 STARTING SKYFARM SYSTEM..."
uvicorn skyfarm.main:app --host 0.0.0.0 --port 8001 > skyfarm.log 2>&1 &
SKYFARM_PID=$!

# Wait for startup
echo "⏳ WAITING FOR SERVICES TO BOOT..."
sleep 10

# Run Operating Loop Simulation
echo "🔄 EXECUTING FULL OPERATING LOOP..."
python3 simulate_full_operating_loop.py

# Final Verification
echo "🔍 VERIFYING PERSISTENT STATE..."
echo "--- SKYFARM OUTBOX ---"
sqlite3 skyfarm.db "SELECT event_type, status FROM integration_outbox;"
echo "--- MNOS EVENT LOG ---"
sqlite3 mnos.db "SELECT id, status FROM event_ingest_log;"

# Cleanup
echo "🛑 SHUTTING DOWN SERVICES..."
kill $MNOS_PID $SKYFARM_PID
echo "✅ ENGINE RUN COMPLETED."
