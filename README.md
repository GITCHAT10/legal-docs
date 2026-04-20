# Maldives Sovereign ESG Cockpit (IFRS S1/S2)

This platform orchestrates fragmented resort operations into an audit-ready ESG data lake, aligned with the 1 January 2026 mandatory reporting transition in the Maldives.

## ESG Orchestration Architecture

The system is organized into three buckets:

### BUCKET A — EXISTING CORE MODULES (Implemented)
- **mRIS (Sovereign Scoring):** HCMI 2.0 aligned engine calculating carbon per occupied room and biodiversity impact. (`backend/app/mris.py`)
- **Shadow Ledger:** Immutable evidence chain using SHA256 hashing for every telemetry record. (`backend/app/ledger.py`)
- **Sovereign Cockpit:** Real-time dashboard for resort management and island-level compliance tracking. (`frontend/src/App.tsx`)
- **MNO Controller:** Multi-tenant island data segregation. (`backend/app/tenant.py`)
- **Environmental Signals:** Tailored Maldives constants (Diesel grid, Desalination). (`backend/app/signals.py`)

### BUCKET B — NEEDED INTEGRATIONS (Implemented as Adapters)
- **PMS/POS API:** Connectors for Opera and FI-ES Andromeda (Occupancy, F&B, Laundry). (`backend/app/integrations/pms.py`)
- **Logistics Hub:** Fuel logs and TravelCO2 flight API integration. (`backend/app/integrations/logistics.py`)
- **Billing/Offset API:** Pushes Carbon Surcharges to folios and executes offset trades. (`backend/app/integrations/billing.py`)
- **Validation Feeds:** AQICN, IQAir, and Meteorological adapters. (`backend/app/integrations/feeds.py`)

### BUCKET C — NARRATIVE / PRESENTATION (Deferred)
- Presentation artifacts (IMF Decks, UN Keynotes, Bond Teasers) are documented as presentation artifacts only and are not part of the codebase.

## Compliance Metrics (CMDA/PCB/CAM)
- **Environmental:** Marine Biodiversity (Coral Health), Climate Resilience, Plastic Waste vs. Recycled.
- **Social:** Gender Equality (30% Female Board Target), Local Supplier Spend.
- **Governance:** Sustainability Policy Compliance, Internal Audit Scores (PCB 2026 Guidelines).

## Local Setup

### Backend (FastAPI)
1. Navigate to the backend directory: `cd backend`
2. Install dependencies: `pip install -r requirements.txt`
3. Run the server: `uvicorn app.main:app --reload`
4. Run tests: `pytest`

### Frontend (React + Vite)
1. Navigate to the frontend directory: `cd frontend`
2. Install dependencies: `npm install`
3. Run the development server: `npm run dev`
4. Build for production: `npm run build`
