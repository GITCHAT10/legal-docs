# SKYFARM <-> MNOS Integration Contract

## Security
- **Authentication**: HMAC-SHA256 signature using a shared secret.
- **Timestamp Validation**: Requests must be within 60 seconds of the current server time to prevent replays.
- **Mandatory Headers**:
  - `X-Signature`: The HMAC signature.
  - `X-Timestamp`: ISO-8601 timestamp in UTC.
  - `X-Request-Id`: Unique UUID for replay protection.
  - `X-Idempotency-Key`: Unique UUID for ensuring exactly-once processing.
  - `X-Correlation-Id`: System-wide trace ID for observability.

## API Endpoints (MNOS Side)
- `POST /integration/v1/events/production`: Ingest production events.
- `GET /mnos/v1/policies/skyfarm`: Retrieve active policy metadata.

## Reliability
- **Timeout**: 5 seconds for all outbound calls from SKYFARM.
- **Retries**: Outbox worker implements exponential backoff (15s, 60s, 300s) for 5xx/408 errors.

## Failure-Mode Matrix
| Failure Scenario | MNOS Status | SKYFARM Handling | User Impact |
| :--- | :--- | :--- | :--- |
| Missing/Invalid Secret | 401 | Immediate Exception | Service halt, requires admin config. |
| Replayed Request | 401 | Immediate Exception | Blocked action, security alert logged. |
| Policy Rejection | 403 | 403 Raised | Action denied by governance rules. |
| Duplicate Event | 200/409 | Original Response | Idempotent success, no side effects. |
| Service Unavailable | 503 | 502/504 Raised | Queued in Outbox for background retry. |
| Request Timeout | N/A | 504 Raised | Queued in Outbox for background retry. |
| Malformed Schema | 422 | 422 Raised | Immediate failure, requires code fix. |

## Verification Proof
- All integration hardening tests PASSED (12/12).
- Mandatory secret enforcement verified: System halts if `SKYFARM_INTEGRATION_SECRET` is missing.
- Traceability verified: `X-Correlation-Id` propagates across all cross-system calls.
