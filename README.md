# iGEO Sovereign Platform - MNOS / ASI Engine

## Overview
This repository contains the **iGEO Sovereign Platform**, a next-generation automated design and infrastructure engine developed for the **Maldives International Group (MIG)** (UEI: 2024PV12395H).

The platform implements the **Maldives NextGen Operating System (MNOS)** architecture, integrating deterministic geometry, real-time fiscal logic (MIRA-compliant), and high-fidelity utility simulations.

## Key Modules
*   **Core Sovereign Layer:** `eleone` (Decision) and `shadow` (Audit Ledger).
*   **ASI Design Pipeline:** `sie` (Geometry), `aegis` (Compliance), and `fce/boq` (Finance).
*   **Infrastructure Ops:** `aquasync` (RO Desalination), `haceoslar` (Energy Sync), and `sewer` (Hydraulic Modeling).

## Getting Started
1.  **Start the Engine:**
    ```bash
    python3 main.py
    ```
2.  **Access the Dashboard:**
    Open `http://localhost:8000/static/index.html` in your browser.
3.  **API Documentation:**
    Refer to `openapi.yaml` for full endpoint specifications.

## Verification
Run the integrated pipeline test to verify all sovereign layers:
```bash
python3 demo_hotel_designer.py
```

---
**Maldives International Group (MIG) Sovereign Property**
