# iMOXON Microservices Architecture

## Overview
iMOXON uses a distributed module pattern (N-DEOS) that acts as a virtualized microservices environment.

## Service Registry
1. **Identity (AEGIS)**: `mnos/modules/aegis/`
2. **Finance (FCE)**: `mnos/modules/finance/`
3. **Commerce Core**: `mnos/modules/imoxon/core/`
4. **Logistics**: `mnos/modules/imoxon/logistics/`
5. **Exchange**: `mnos/modules/exchange/`
6. **Super App SDK**: `mnos/modules/bubble/`

## Communication
- **Synchronous**: REST/FastAPI via `ExecutionGuard`.
- **Asynchronous**: `DistributedEventBus` for cross-module coordination.

## Security
- All internal communication requires a signed sovereign context.
- External entry via `APIGatewayControlPlane`.
