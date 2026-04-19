# MNOS LIFELINE

MNOS-native sovereign healthcare execution system.

## Architecture: CORE governs, INTERFACES connect, MODULES execute

### MNOS Transaction Order
All writes follow this strict order:
1. **AEGIS verify**: Identity and role enforcement.
2. **ELEONE decide**: Legality and policy engine.
3. **Module DB write**: Execution logic.
4. **EVENTS publish**: Async orchestration.
5. **SHADOW commit**: Immutable audit + evidence chain.
6. **FCE calculate**: Financial clearance (where applicable).

### Directory Structure
- `/mnos/core`: AEGIS, SHADOW, ELEONE, EVENTS, FCE
- `/mnos/interfaces`: API Gateway, Portals
- `/mnos/modules`: LIFELINE, AASANDHA, PHARMACY, etc.
- `/mnos/shared/sdk`: MNOS Client and standard models.

### Setup
```bash
./scripts/run_engine.sh
```
