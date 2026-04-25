# ADMIRALDA PBX - Production Deployment

## Staging Deployment
To deploy to staging using Docker Compose:
\`\`\`bash
docker-compose up --build
\`\`\`

## Production Deployment
1. Build the production image:
\`\`\`bash
docker build -t admiralda-pbx:latest -f admiralda_pbx/Dockerfile .
\`\`\`
2. Configure environment variables in Kubernetes/ECS:
   - \`MNOS_GATEWAY_URL\`: Internal URL of the MNOS API.
   - \`TELECOM_PROVIDER\`: e.g., \`TWILIO\`.
   - \`DATABASE_URL\`: Postgres URL for production persistence.

## Monitoring
- Health check: \`GET /health\`
- Provider health: \`GET /api/v1/operator/health/telecom\`
- Structured logs are emitted to stdout.
