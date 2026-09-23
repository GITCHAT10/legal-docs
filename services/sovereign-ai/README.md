# MIG Sovereign AI Control Plane

Production-oriented control plane for specialized AI agents operating across MIG, SALA Hotels & Resorts Maldives, United Transport, ILUVIA, iMOXON and AIG.

## Core principles

- Human authority remains final for regulated, financial, legal, safety and irreversible actions.
- Agents never write directly to the canonical ledger.
- Every task is tenant-scoped, policy-checked, idempotent and audit logged.
- Tool access is allow-listed per agent.
- High-risk actions require approval before execution.
- The shared PostgreSQL ledger remains the source of financial truth.

## Initial modules

- Agent Registry
- Department Registry
- Task Orchestrator
- Policy and Approval Gate
- Immutable Audit Events
- Idempotency Controls
- Multi-company tenant isolation
- Health and operational endpoints

## Run locally

```bash
cp .env.example .env
docker compose up --build
```

API: `http://localhost:8088`
Docs: `http://localhost:8088/docs`

## Main endpoints

- `POST /v1/agents`
- `GET /v1/agents`
- `POST /v1/tasks`
- `POST /v1/tasks/{task_id}/approve`
- `POST /v1/tasks/{task_id}/execute`
- `GET /v1/tasks/{task_id}`
- `GET /v1/audit-events`

This is Phase 1 of the agent operating layer. It is intentionally isolated from unrestricted production tools until policy adapters and service credentials are configured.