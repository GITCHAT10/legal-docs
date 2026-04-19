# MNOS LIFELINE Folder Doctrine

> **CORE governs → INTERFACES connect → MODULES execute**

## Service/Module Layers
Each service or module should always contain these layers:
- **/api**: External contract
- **/service**: Business logic
- **/repository**: Database access
- **/models**: Domain models
- **/events**: Publish/consume events
- **/tests**: Module-owned tests

## Rules
- No module writes directly into another module's tables.
- All cross-domain actions happen through APIs or events.
- Core services (AEGIS, SHADOW, ELEONE, EVENTS, FCE) are national control organs.
- Interfaces are the human-facing and external-facing entry points.
- Modules execute domain work.
- All state-changing events should be audit-locked through SHADOW.
