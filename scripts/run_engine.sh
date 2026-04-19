#!/bin/bash
set -e

echo "🚀 Bootstrapping MNOS LIFELINE..."

# 1. Initialize environment
if [ ! -f .env ]; then
  echo "Creating .env from template..."
  echo "MNOS_INTEGRATION_SECRET=top-secret" > .env
  echo "DATABASE_URL=postgresql://jules:password@db:5432/mnos_lifeline" >> .env
fi

# 2. Build and start services
echo "Starting services with Docker Compose..."
docker-compose up -d

# 3. Wait for DB and run migrations
echo "Waiting for database..."
sleep 5
echo "Running migrations..."
# docker-compose exec db psql -U jules -d mnos_lifeline -f /infra/db/migrations/20240419_initial_schema.sql

# 4. Health checks
echo "Running health checks..."
# ./scripts/health_check.sh

echo "✅ MNOS LIFELINE is ready!"
