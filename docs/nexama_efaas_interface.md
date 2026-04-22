# NEXAMA ↔ eFaas Sovereign Handshake Protocol (MDS v1.0)

## 1. Overview
This document specifies the integration protocol between **NEXAMA HEALTH CARE ENGINE** and the **Maldives National Digital Identity (eFaas)** portal. All integrations must strictly adhere to MNOS Sovereign Law (AEGIS-SHADOW).

## 2. Authentication Flow (OIDC)
NEXAMA acts as a Relying Party (RP) to the eFaas OpenID Connect Provider (OP).

*   **Discovery URL**: `https://efaas.egov.mv/.well-known/openid-configuration`
*   **Scopes Required**: `openid`, `profile`, `national_id`, `digital_signature`

## 3. Mandatory Handshake Headers
Every clinical patient registration request to NEXAMA must include:

```http
X-EFAAS-TOKEN: <JWS_Signed_Identity_Token>
Authorization: Bearer <AEGIS_Device_Session_Token>
```

## 4. Biometric-Linked Queue (Patent AL)
To activate a physical clinic queue token, the eFaas `sub` (Subject ID) must be cryptographically bound to the NEXAMA biometric hash.

### API Endpoint
`GET /api/nexama/queue/token?efaas_id={id}&facility_id={fid}`

## 5. Security Guardrails
1.  **Fail-Closed**: If the eFaas token signature validation fails, the entire NEXAMA transaction is halted.
2.  **SHADOW Audit**: Every eFaas authentication event is logged into the SHADOW immutable ledger with a `trace_id` linked to the patient's national ID.
3.  **Data Sovereignty**: eFaas profile data is never stored outside the Maldives jurisdiction.

## 6. Verification
Developers can use the `scripts/verify_nexama.py` tool to simulate an eFaas handshake in the staging environment.
