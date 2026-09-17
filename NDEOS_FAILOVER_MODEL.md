# N-DEOS FAILOVER & RECOVERY MODEL

## 1. Island Disconnect
- **Detection:** Gateway heartbeat failure.
- **Action:** Edge node switches to `OFFLINE_AUTONOMOUS` mode.
- **Result:** Transactions recorded in `LOCAL_EVENT_BUFFER`.

## 2. Island Reconnect
- **Detection:** Sync agent detects core heartbeat.
- **Action:** `BATCH_SYNCHRONIZATION` protocol initiated.
- **Verification:** `SHADOW_CHAIN_MERGE` with re-hashing for integrity.

## 3. Data Integrity Break
- **Detection:** Shadow certification hash mismatch.
- **Action:** `AUTO_ROLLBACK` to last known valid block.
- **Result:** `EVENT_REPLAY` triggered for affected partition.
