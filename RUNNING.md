# BUILDX HARDENED — Running Instructions

This repository contains a production-ready MNOS execution engine scaffold.

## 🐳 Docker Compose (Recommended)

1. Build and start the entire stack:
   ```bash
   docker compose up --build
   ```
2. Verify system health:
   ```bash
   ./scripts/validate_stack.sh
   ```

## 🚀 Local Bootstrap (without Docker)

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Ensure Redis is installed locally (optional but recommended for event pipeline).
3. Run the bootstrap script:
   ```bash
   ./run_engine.sh
   ```
4. Check the logs in the root directory (`gateway.log`, `eleone.log`, etc.).

## 🧪 Running Tests

```bash
python3 -m pytest
```
Note: Some integration tests require services to be up or mocks to be enabled.
