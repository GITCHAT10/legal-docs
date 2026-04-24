# 📘 MIG INTEGRATION PLAYBOOK

ENTITY: MALDIVES INTERNATIONAL GROUP (MIG)
STATUS: DEPLOYABLE

## 1. INFRASTRUCTURE SETUP
1. **ORBAN VPN**: Establish secure tunnel to MIG Cloud Core.
2. **AEGIS Identity**: Register resort server hardware ID in Sovereign Registry.

## 2. DATA PIPELINE (PIO)
- **Primary**: Real-time webhook ingestion (Ed25519 Signed).
- **Fallback**: SFTP CSV Export (Hourly) for legacy Oracle/Mews versions.

## 3. RECONCILIATION WORKFLOW
1. **Detect**: System flags variance between PMS charge and FCE Truth.
2. **Resolve**: Follow 'Reversal-Only' policy. Never edit a posted record.
3. **Seal**: Confirm resolution in SHADOW ledger.

## 4. CONTACTS
- **Core Architecture**: JULES (Sovereign Execution Agent)
- **Authority**: ASI CEO / MIG Command
