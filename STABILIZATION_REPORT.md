# 🧾 SKYFARM STABILIZATION REPORT

## 1. Changed Files

### SKYFARM (Execution Stack)
- `skyfarm/main.py`: Disabled experimental SXOS modules (Supply, ESG, Metrics, etc.).
- `skyfarm/integration/service.py`: Hardened security, removed fallback secrets, added `ALLOW_INSECURE_DEV` and `ALLOW_MANUAL_OVERRIDE` flags.
- `skyfarm/integration/router.py`: Enforced strict (2, 5) timeouts and explicit HTTP error propagation.

### MNOS (Governance Stack)
- `mnos/iocs/*`: Added APOLLO Control Plane for node health and policy-as-code.
- `mnos/silvia/*`: Added SILVIA Decision Layer for explainable insights.
- `mnos/twin/models.py`: Extended Digital Twin with Resource Flow modeling.
- `mnos/database.py`: Fixed model registration and dependency ordering.
- `mnos/main.py`: Integrated new governance routers.

### Quality & Reliability
- `tests/test_integration_failure_paths.py`: Verified 401 and timeout handling.
- `tests/test_outbox_retry.py`: Verified exponential backoff (15s, 60s, 300s).
- `tests/test_integration_hardening.py`: Updated existing tests for strict status checking.

## 2. Integration Contract (Final)

### Outbound (SKYFARM -> MNOS)
- **Endpoint**: `POST /integration/v1/events/production`
- **Auth**: HMAC-SHA256 Canonical Signature (`X-Signature`)
- **Headers**: `X-Timestamp` (60s window), `X-Request-Id`, `X-Idempotency-Key`
- **Pattern**: Transactional Outbox (Async)

### Inbound (MNOS -> SKYFARM)
- **Policies**: `GET /mnos/v1/policies/skyfarm`
- **Signals**: `GET /mnos/v1/signals/skyfarm`
- **Control**: `POST /iocs/v1/ping` (Heartbeat)

## 3. Failure-Mode Matrix

| Scenario          | Behavior                                      |
| ----------------- | --------------------------------------------- |
| MNOS down         | Local event queuing + Retry (15s/60s/300s)    |
| invalid signature | MNOS returns 401; SKYFARM logs + halts event  |
| duplicate event   | Idempotency key match; returns cached response|
| timeout           | Retry via Outbox Worker (max 4 attempts)      |
| policy reject     | Propagate real HTTP status to caller          |

## 4. Remaining Risks
- **Clock Drift**: Extreme clock drift (>60s) between Edge and Core will break HMAC validation. NTP sync is mandatory.
- **SQLite Concurrency**: Current dev mode uses SQLite; production deployment must migrate to PostgreSQL for high-volume outbox processing.
- **Manual Overrides**: `ALLOW_MANUAL_OVERRIDE` allows bypassing MNOS signals; audit logs of these events must be reviewed manually.
