# HMS <-> iMOXON API Airlock Specification

## Authentication Handshake
1. **Sender**: Generates payload + timestamp + nonce + trace_id.
2. **Signature**: Ed25519 sign(payload + header).
3. **Receiver (Airlock)**:
   - Verifies node_id in NodeRegistry.
   - Verifies Ed25519 signature using registered public key.
   - Checks nonce has not been used.
   - Checks timestamp drift < 60s.
   - Logs result to AIGShadow.

## API Scopes

### HMS Permissions
- `rfq:create`: Post new RFQ to iMOXON.
- `quotes:read`: Get quote summaries from iMOXON.
- `order:create`: Approve quote and create order.
- `delivery:confirm`: Confirm receipt of goods.

### Vendor/iMOXON Permissions
- `quote:create`: Post quote in response to RFQ.
- `shipment:update`: Update status of active deliveries.

## Data Sovereignty
- Guest data NEVER leaves HMS.
- Quotes contain only generic IDs, landed cost, and SLA.
