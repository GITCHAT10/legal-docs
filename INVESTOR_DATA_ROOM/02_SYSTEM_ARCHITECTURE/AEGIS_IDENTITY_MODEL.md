# 🛡️ AEGIS IDENTITY MODEL

## Hardware-Bound Sovereignty
AEGIS enforces absolute server-side trust. No identity or session is valid without a verified binding to an authorized hardware device.

## Security Controls
- **HMAC-SHA256 Sessions**: Every API request must carry a signed session context.
- **Nonce Tracking**: Mandatory replay resistance with 60-second temporal windows.
- **Server-Side Registry**: Hardware IDs (Nexus DNA) are verified against an HSM-backed registry.
- **Biometric Integration**: High-risk actions require eFaas or biometric secondary validation.

## Governance
Role-based access is resolved server-side; client-provided roles are strictly rejected.
