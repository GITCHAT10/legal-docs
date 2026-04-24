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

## Carbon Integration (SALA x SKYFARM)
- `POST /integration/v1/carbon/retire`: Retire offsets for SALA guests.
- **Payload**: `{"guest_name": str, "amount_kg": float, "correlation_id": str}`

## Reliability
- **Timeout**: 5 seconds for all outbound calls from SKYFARM.
- **Retries**: 3 attempts with exponential backoff for transient errors (408, 502, 503, 504).

## Failure-Mode Matrix
| Scenario | MNOS Status | SKYFARM Exception | Handling |
| :--- | :--- | :--- | :--- |
| Invalid Secret | 401 | 401 Unauthorized | Critical alert, halt process |
| Signature Mismatch | 401 | 401 Unauthorized | Log security breach |
| Policy Rejection | 403 | 403 Forbidden | Halt execution |
| Idempotency Hit | 200/409 | Original Response | Skip processing |
| Timeout | N/A | 504 Gateway Timeout | Background Retry |
| Server Error | 500/502 | 502 Bad Gateway | Background Retry |

## Testing Summary
- **Hardening Tests**: 100% PASS (401, Timeout, Invalid Signature)
- **Compliance Suite**: 100% PASS
- **Economy Simulation**: 100% PASS (Closed loop verified)
