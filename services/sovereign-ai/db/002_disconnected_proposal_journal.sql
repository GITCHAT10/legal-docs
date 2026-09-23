CREATE SCHEMA IF NOT EXISTS staging_journal;

CREATE TABLE staging_journal.agent_proposals (
    id BIGSERIAL PRIMARY KEY,
    proposal_hash CHAR(64) NOT NULL UNIQUE,
    idempotency_key VARCHAR(255) NOT NULL,
    legal_entity_id UUID NOT NULL,
    origin_agent_id UUID NOT NULL,
    currency CHAR(3) NOT NULL,
    effective_date DATE NOT NULL,
    raw_payload JSONB NOT NULL,
    canonical_payload JSONB NOT NULL,
    risk_class VARCHAR(20) NOT NULL,
    policy_version VARCHAR(32) NOT NULL,
    required_approvals SMALLINT NOT NULL,
    decision_status VARCHAR(30) NOT NULL DEFAULT 'AWAITING_APPROVAL',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_agent_proposal_entity_key UNIQUE (legal_entity_id, idempotency_key),
    CONSTRAINT chk_proposal_currency CHECK (currency IN ('USD', 'MVR')),
    CONSTRAINT chk_proposal_risk CHECK (risk_class IN ('CLASS_2', 'CLASS_3', 'CLASS_4')),
    CONSTRAINT chk_required_approvals CHECK (required_approvals BETWEEN 1 AND 3),
    CONSTRAINT chk_proposal_status CHECK (decision_status IN (
        'AWAITING_APPROVAL', 'APPROVED_PENDING_POST', 'REJECTED', 'POSTED'
    ))
);

CREATE TABLE staging_journal.proposal_lines (
    id BIGSERIAL PRIMARY KEY,
    proposal_id BIGINT NOT NULL REFERENCES staging_journal.agent_proposals(id) ON DELETE RESTRICT,
    line_number INTEGER NOT NULL,
    account_code VARCHAR(20) NOT NULL,
    debit NUMERIC(20, 2) NOT NULL DEFAULT 0.00,
    credit NUMERIC(20, 2) NOT NULL DEFAULT 0.00,
    CONSTRAINT uq_proposal_line UNIQUE (proposal_id, line_number),
    CONSTRAINT chk_line_nonnegative CHECK (debit >= 0.00 AND credit >= 0.00),
    CONSTRAINT chk_line_exclusivity CHECK (
        (debit > 0.00 AND credit = 0.00) OR
        (credit > 0.00 AND debit = 0.00)
    )
);

CREATE TABLE staging_journal.immutable_decision_evidence (
    id BIGSERIAL PRIMARY KEY,
    proposal_id BIGINT NOT NULL REFERENCES staging_journal.agent_proposals(id) ON DELETE RESTRICT,
    event_type VARCHAR(40) NOT NULL,
    previous_proof_hash CHAR(64),
    evidence_proof_hash CHAR(64) NOT NULL UNIQUE,
    actor_id VARCHAR(255) NOT NULL,
    human_signatures JSONB,
    evidence_payload JSONB NOT NULL,
    validated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_proposals_status_created
    ON staging_journal.agent_proposals (decision_status, created_at);
CREATE INDEX idx_proposals_entity_effective
    ON staging_journal.agent_proposals (legal_entity_id, effective_date);
CREATE INDEX idx_evidence_proposal_time
    ON staging_journal.immutable_decision_evidence (proposal_id, validated_at);

-- Append-only enforcement. The posting adapter may append evidence and transition
-- decision_status through a separately controlled SECURITY DEFINER function, but
-- ordinary application roles receive no UPDATE or DELETE privilege.
REVOKE UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA staging_journal FROM PUBLIC;
