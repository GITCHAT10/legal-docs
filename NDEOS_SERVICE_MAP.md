# N-DEOS EVENT TOPOLOGY & SERVICE MAP

## Event Partitions
- `PARTITION_MALE`: Central business and government transactions.
- `PARTITION_ATOLL_[ID]`: Regional commerce and local logistics.
- `PARTITION_RESORT_[ID]`: Island-specific procurement and guest services.
- `PARTITION_PORT_[ID]`: Customs and inbound cargo clearance.

## Service Replay Engine
1. **Initialize:** Load snapshots from SHADOW.
2. **Replay:** Stream events from specified timestamp.
3. **Validate:** Compare recomputed state with certification hashes.
4. **Certified:** State is court-admissible and forensics-grade.

## Deployment Map (Phase 1)
- **Primary:** NCIT Malé Cloud.
- **Edges:** 10 Selected Resorts (Pilot) + 3 International Ports (Inbound).
- **Logistics:** Dhiraagu/Ooredoo M2M connectivity for vessel edges.
