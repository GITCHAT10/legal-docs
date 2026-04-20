# Maldives Sovereign Environmental Backbone

This repository contains the core modules and integration adapters for the Maldives sovereign environmental scoring and telemetry system.

## Architecture Classification

The system is organized into three buckets:

### BUCKET A — EXISTING CORE MODULES (Implemented)
- **mRIS (Maldives Remote Impact Scoring):** Core engine for calculating environmental footprint based on sovereign signals. (`backend/app/mris.py`)
- **Sovereign Cockpit:** Unified dashboard for real-time visualization. (`frontend/src/App.tsx`)
- **Telemetry Ingestion:** Unified interface for sensor data streams. (`backend/app/telemetry.py`)
- **Signals:** Maldives-specific constants for energy, ocean, air, and waste. (`backend/app/signals.py`)
- **Backbone Components:** Stubs for Ledger (Blockchain Anchor), Anomaly Engine (Green HACCP), and Compliance Switchboard.

### BUCKET B — NEEDED INTEGRATIONS (Implemented as Adapters)
- **Ministry Connectors:** Finance and Environment dashboard access paths. (`backend/app/integrations/ministry.py`)
- **External Feeds:** Adapters for AQICN, IQAir, and Meteorological data. (`backend/app/integrations/feeds.py`)
- **Field Nodes:** LagoonBin and resort edge node connectors. (`backend/app/integrations/nodes.py`)

### BUCKET C — NARRATIVE / PRESENTATION (Deferred)
- Presentation artifacts (Decks, Keynotes, Press Releases) are not part of this implementation.

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

## Configuration

Environmental signals and emission factors are configured in `backend/app/signals.py`. These constants are derived from local Maldives diesel-grid data, desalination energy intensity, and maritime logistics.
