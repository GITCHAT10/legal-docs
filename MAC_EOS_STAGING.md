# MAC EOS staging inspection console

This is a separate, read-only entrypoint over the real backend code. It is NOT
a complete hospitality UAT console and does not grant access to legacy APIs.
No property or guest records are seeded. SALA_OMAGILI_TEST is a scope label,
not a claim that an operational test property exists.

## Security boundary

Inspection found simulated authentication in `AegisIdentityGateway.login`,
predictable `VALID_SIG_FOR_...` validation in `main.py`, in-memory sessions,
and a development secret fallback. Do not expose `main:app` to staff or the
Internet until those have been independently remediated and tested.

The console imports backend objects in a separate process but mounts none of
the legacy routes. It returns only code identity and audit-chain status, never
bookings, guest records, finances, or global property records. All four roles
have the same inspection access; manager alone can inspect login audit records.
These roles grant no operational permissions in MAC EOS or AEGIS.

New staging passwords use scrypt, random salts, and no default credentials.
Opaque session tokens are stored hashed in SQLite, expire after 30 minutes,
and are revoked on logout or account deactivation. Cookies are HttpOnly,
Secure, SameSite=Strict. POSTs require an exact configured Origin. Five failed
logins lock an account for 15 minutes. Audit is durable access logging, NOT a
cryptographically sealed SHADOW ledger or production-grade audit claim.

## Deployment prerequisites (not yet deployed)

An approved private HTTPS Python hosting target and persistent disk are needed.
Run separately from production with no bank, payment, message or production
database credentials. Enforce edge IP rate limits and a 4 KiB request-body cap
(including chunked bodies) before exposing the service. Restrict upstream host
headers to the configured hostname; terminate TLS at the approved proxy.
Use one worker, a non-root service account, private filesystem permissions and
an independently reviewed dependency lock before hosted release.

Set MAC_EOS_ENV=staging, MAC_EOS_STAGING_ORIGIN to the exact HTTPS origin,
and MAC_EOS_STAGING_DB to an absolute path on a private persistent volume.
The parent directory must already exist and be restricted to the service user.

Provision individual accounts interactively on that host:

    python staging_console.py USERNAME manager

Other roles: front_desk, housekeeping, finance. Do not pass passwords on the
command line or commit the database. Use a unique password of 16+ characters.
No invitation or email is sent. Account creation requires approved staff scope.

Run only the isolated entrypoint:

    uvicorn staging_console:create_app --factory --host 127.0.0.1 --port 8080 --workers 1

Never substitute `main:app`. The proxy must forward only to this entrypoint.
Disable an account by setting users.active=0 via restricted database
administration; this invalidates its existing sessions on their next request.

## Verification and release gate

    python -m pytest tests/test_staging_console.py -q
    python -m pytest -q
    ruff check staging_console.py tests/test_staging_console.py

Browser verification on the actual HTTPS host, independent security review,
account setup and staff acceptance remain mandatory. No production promotion.
Rollback: stop the staging process and remove its proxy route; preserve the
private auth/audit database for investigation. No operational data is changed.
