# N-DEOS: National Distributed Economic Operating System (Maldives)

## 1. Architecture Diagram
[Intelligence Layer: Mercury-Vine] -> [Control Plane: APOLLO] -> [Escrow: FCE] -> [Logistics: UT] -> [Audit: SHADOW]

## 2. Service Map
- **Governance**: `/v1/governance/` (Multi-sig, Traces, Approvals)
- **Mobility**: `/v1/ut/` (Dispatch, Reroute, Handshake)
- **Finance**: `/v1/fce/` (Escrow, Tax-split, Settlement)
- **Intelligence**: `/v1/imoxon/` (AI-ECON, Forecasting)
- **Edge**: `/v1/edge/` (Offline Enqueue, Ordered Replay)

## 3. Event Topology (Durable Bus)
- **Partitioning**: Island-ID based sharding for high concurrency and isolation.
- **Persistence**: Durable event logs anchored in SHADOW.
- **Protocol**: Kafka-style replayable streams.

## 4. Deployment Topology
- **Central (Malé)**: Authority Node, MIRA Bridge, National Ledger.
- **Atoll Nodes**: Regional Hubs for Supply Chain and Logistics routing.
- **Edge Nodes (Resort/Port)**: Local execution, offline-first buffer, physical delivery tracking (GRN).

## 5. Failover Model
- **Offline-First**: Distributed nodes enqueue operations locally during uplink failure.
- **Deterministic Replay**: Ordered sync by sequence number ensuring core/edge state parity.
- **Zero-Point Hold**: 24h stability buffer before state finalization during recovery.

## 6. Financial Waterfall (QT-SIM)
- **Gross Revenue** -> **17% TGST** -> **5% Platform Fee** -> **Lease** -> **Fuel** -> **Net Payout**

## 7. Legal Grade Audit
- **SHADOW Chain**: Prev-hash + Payload-digest + Trace-ID → Current-hash.
- **Evidence Bundles**: Court-admissible export formats for regulatory compliance.
- **AEGIS**: Identity-bound signatures for every state mutation.
