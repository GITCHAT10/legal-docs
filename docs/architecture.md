# MNOS LIFELINE Module Map

> **CORE governs → INTERFACES connect → MODULES execute**

---

## 🏛️ 1. MNOS BASE STRUCTURE

```text
/mnos
  /core
    /aegis
    /shadow
    /eleone
    /events
    /fce

  /interfaces
    /bubble
    /doctor_portal
    /nurse_portal
    /patient_portal
    /admin_portal
    /api_gateway

  /modules
    /lifeline
    /aasandha
    /pharmacy
    /diagnostics
    /finance
    /telemedicine
    /public_health
    /inventory
    /identity_bridge
    /payments
    /notifications
    /analytics
```

---

## 🧬 2. CORE LAYER

### AEGIS
Identity, authentication, practitioner trust.
- doctor login
- nurse/admin roles
- patient ID verification
- token issuance
- facility identity

### SHADOW
Immutable audit and evidence chain.
- access logs
- prescription sign events
- AI divergence logs
- insurance claim trace
- forensic replay

### ELEONE
Policy and legality engine.
- doctor must sign
- only licensed prescribers can prescribe
- patient-facing AI restrictions
- insurance rule validation
- country policy logic

### EVENTS
Real-time orchestration bus.
- triggers downstream modules
- event fanout
- async workflows
- alert propagation

### FCE
Financial calculation engine.
- invoice totals
- copay logic
- insurance split
- provider settlement logic
- MVR handling

---

## 🫧 3. INTERFACE LAYER

- **BUBBLE**: Unified interaction layer.
- **Doctor Portal**: For consultations, AI review, prescriptions, signatures.
- **Nurse Portal**: For triage, vitals, intake, queue movement.
- **Patient Portal**: For appointments, records access, payment, notifications.
- **Admin Portal**: For claims, staff management, reporting, audits.
- **API Gateway**: Single secured entry for all module communication.

---

## 🏥 4. EXECUTION MODULES

### 4.1 LIFELINE
The clinical core.
- patient registration
- consultations
- doctor notes
- prescriptions
- treatment plans
- case history

### 4.2 AASANDHA
Insurance and national reimbursement module.
- eligibility check
- pre-authorization
- claim submission
- reimbursement workflow
- settlement tracking

### 4.3 PHARMACY
Medication and dispensing engine.
- medicine catalog
- dispense tracking
- stock management
- interaction checking
- low-stock alerts

### 4.4 DIAGNOSTICS
Lab, imaging, and reports.
- test orders
- result ingestion
- DICOM routing
- report attachment
- abnormality flags

### 4.5 FINANCE
Billing and revenue module.
- patient billing
- copay calculation
- invoice generation
- provider payout ledger
- cash/bank reconciliation

### 4.6 TELEMEDICINE
Remote specialist support.
- remote consults
- specialist referrals
- island-to-Malé escalation
- document/image sharing

### 4.7 PUBLIC_HEALTH
National pattern intelligence.
- anonymized case clustering
- outbreak early warning
- trend analysis
- climate-health correlation

### 4.8 INVENTORY
General medical supply chain.
- non-pharmacy stock
- IV fluids, gloves, kits
- transfer between facilities
- usage forecasting

### 4.9 IDENTITY_BRIDGE
Government identity connection layer.
- e-Faas integration
- national ID lookups
- facility verification
- practitioner registry sync

### 4.10 PAYMENTS
Bank and wallet connection layer.
- copay payment
- refunds
- provider settlement rails
- receipt confirmation

### 4.11 NOTIFICATIONS
Communications layer.
- appointment reminders
- claim status updates
- critical alerts
- low stock notifications

### 4.12 ANALYTICS
Decision dashboard layer.
- KPI tracking
- wait time analysis
- claim efficiency
- outbreak and stock trends
