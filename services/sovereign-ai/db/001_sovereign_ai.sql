CREATE SCHEMA IF NOT EXISTS sovereign_ai;

CREATE TABLE IF NOT EXISTS sovereign_ai.agent (
    agent_id UUID PRIMARY KEY,
    legal_entity_id UUID NOT NULL,
    code VARCHAR(64) NOT NULL,
    name VARCHAR(120) NOT NULL,
    department VARCHAR(80) NOT NULL,
    allowed_tools JSONB NOT NULL DEFAULT '[]'::jsonb,
    max_risk VARCHAR(16) NOT NULL CHECK (max_risk IN ('LOW','MEDIUM','HIGH','CRITICAL')),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (legal_entity_id, code)
);

CREATE TABLE IF NOT EXISTS sovereign_ai.task (
    task_id UUID PRIMARY KEY,
    legal_entity_id UUID NOT NULL,
    agent_id UUID NOT NULL REFERENCES sovereign_ai.agent(agent_id),
    action VARCHAR(120) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    risk VARCHAR(16) NOT NULL CHECK (risk IN ('LOW','MEDIUM','HIGH','CRITICAL')),
    state VARCHAR(32) NOT NULL,
    idempotency_key VARCHAR(128) NOT NULL,
    requested_by VARCHAR(160) NOT NULL,
    approved_by VARCHAR(160),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    executed_at TIMESTAMPTZ,
    UNIQUE (legal_entity_id, idempotency_key)
);

CREATE TABLE IF NOT EXISTS sovereign_ai.audit_event (
    audit_event_id UUID PRIMARY KEY,
    legal_entity_id UUID NOT NULL,
    event_type VARCHAR(80) NOT NULL,
    actor VARCHAR(160) NOT NULL,
    object_id UUID NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    previous_hash CHAR(64) NOT NULL,
    event_hash CHAR(64) NOT NULL UNIQUE,
    details JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_ai_task_entity_state ON sovereign_ai.task (legal_entity_id, state, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_ai_audit_entity_time ON sovereign_ai.audit_event (legal_entity_id, occurred_at DESC);

REVOKE UPDATE, DELETE ON sovereign_ai.audit_event FROM PUBLIC;
