# N-DEOS: National Distributed Economic Operating System

## Architecture Overview
iMOXON N-DEOS is a multi-island distributed economic network designed for the Maldives. It eliminates centralized dependencies through Edge-Node autonomy.

### Service Map
- **Core Governance**: MNOS Core (Malé Central Hub)
- **Edge Nodes**: Distributed instances at Atolls, Resorts, and Ports.
- **Economic Intelligence**: AI-ECON (Demand, Procurement, Pricing).
- **Financial Clearing**: FCE Clearing (Multi-party settlements, T+1).
- **Mobility Control**: UT Sovereign Control Tower.

### Event Topology (Durable Bus)
1. **Partitioning**: Events are partitioned by Island ID to ensure local performance and isolation.
2. **Replayability**: Every event is durable and replayable for system recovery and audit.
3. **Idempotency**: All operations utilize `trace_id` for replay protection.

### Failover Model
- **Disconnected Mode**: Edge nodes operate offline using a local queue buffer.
- **Burst Sync**: State-changing events are synchronized to the Core when connectivity is restored.
- **Local Fallback**: Critical infrastructure (Power, Water, Mobility) maintains local execution logic.

### Deployment Topology
- **Malé Node**: Primary financial clearing and cross-atoll orchestration.
- **Atoll Nodes**: Regional logistics and supply chain management.
- **Resort/Port Nodes**: Operational execution (Guest services, Fueling, Dispatch).

### Sovereign Proof
- **Legal SHADOW**: Audit bundles are court-admissible with batches verification hashes.
- **AEGIS**: Identity enforcement across all distributed nodes.
