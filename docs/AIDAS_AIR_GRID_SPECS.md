# A.I.D.A.S. AIR TRAFFIC COMMAND DASHBOARD — PRODUCTION SPEC

## Purpose
Real-time sovereign intake system transforming global flight data into orchestrated island dispatch.

## 1. Core Data Entities
- **Air Corridor**: Strategic routes (e.g., INDIA_SOUTH, GCC_DXB) with priority tiers and preferred arrival windows.
- **Flight Arrival Stream**: Real-time tracking of flights (airline, status, delay, pax count).
- **Arrival Window Cluster**: Groups arrivals for optimized UT transfer assignment.
- **UT Dispatch Queue**: Real-time assignment of speedboat/seaplane based on capacity and segment requirements.
- **Revenue-Pulse**: Dynamic pricing adjustments based on load (>85%) and urgency (<30min arrival).

## 2. Decision Engine Logic (AirGridEngine)
- **Ingestion**: Normalize flight data from AIR CLOUD adapters.
- **Clustering**: Match flights to arrival windows.
- **Assignment**: Trigger UT transfer dispatch based on corridor rules.
- **Dynamic Pricing**: Apply multipliers (up to 1.25x) via FCE integration.
- **Audit**: Commit truth-points to SHADOW (e.g., AIR_GRID_FLIGHT_LANDED).

## 3. API & WebSockets
- `/ws/air-grid/dashboard`: Real-time stream of arrivals and dispatch status.
- Commands for manual override and alert acknowledgment.

## 4. RBAC Roles
- `ops_lead`: Operational control and manual overrides.
- `air_grid_controller`: Real-time monitoring and alert acknowledgment.
- `admin`: Full system configuration.

## 5. Truth-Point Events
- AIR_GRID_FLIGHT_LANDED
- AIR_GRID_UT_DISPATCHED
- AIR_GRID_DYNAMIC_PRICING_APPLIED
- AIR_GRID_MANUAL_OVERRIDE
