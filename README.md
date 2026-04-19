# BUILDX — Backend Microservice Scaffold

Backend microservice scaffold with gateway, core services, compose skeleton, and local bootstrap.

## 🧱 Architecture

- **Gateway**: Entry point for routing and proxying.
- **ELEONE**: Decision engine.
- **SHADOW**: Audit + hash chain ledger.
- **SVD**: Verification engine.
- **SAL**: Standard Audit Log.
- **BFI**: Banking adapter.
- **Edge Node**: IoT inference placeholder.
- **Event Pipeline**: Redis-backed event worker.

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Redis (optional for local event worker)
- Docker & Docker Compose (for containerized deployment)

### Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the system:
   ```bash
   ./run_engine.sh
   ```

3. Run tests:
   ```bash
   pytest
   ```

### Docker Deployment

```bash
docker-compose up --build
```

## 📜 Standards

- Every service exposes a `/health` endpoint.
- Standardized port mapping for local development (8000-8006).
- Resilient proxy logic in the Gateway.
