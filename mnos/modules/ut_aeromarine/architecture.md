# UT AEROMARINE Architecture

## Components
1. **Mission Planner**: Central workflow engine for hybrid air-sea operations.
2. **Compliance Gate**: Final validation layer enforcing MNOS operating rules.
3. **Device Registry**: Verified inventory of all air and sea assets.
4. **Telemetry Watchdog**: Real-time safety monitor with multi-parameter breach detection.
5. **Shadow Logger**: Automated audit-trail generator for every mission state transition.
6. **FCE Billing Gate**: Financial controls preventing commercial release without a sealed audit pack.

## Data Flow
Alert → Mission Creation → Route Planning → Compliance Check → SHADOW Pre-hash → Launch → Telemetry Monitoring → Recovery → SHADOW Seal → FCE Release.
