-- MIG SOVEREIGN INFRA SCHEMA (BUILD-X)
-- MALDIVES INTERNATIONAL GROUP PVT LTD

CREATE TABLE IF NOT EXISTS aegis_identities (
    identity_id UUID PRIMARY KEY,
    national_id VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS aegis_devices (
    device_id VARCHAR(50) PRIMARY KEY,
    identity_id UUID REFERENCES aegis_identities(identity_id),
    hardware_hash VARCHAR(64) NOT NULL,
    last_seen TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS shadow_ledger (
    entry_id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    previous_hash VARCHAR(64) NOT NULL,
    current_hash VARCHAR(64) NOT NULL,
    actor_id VARCHAR(100),
    objective_code VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS buildx_projects (
    project_id UUID PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL,
    authority_id UUID REFERENCES aegis_identities(identity_id),
    status VARCHAR(50) DEFAULT 'DREAMING'
);

CREATE TABLE IF NOT EXISTS buildx_utility_logs (
    log_id BIGSERIAL PRIMARY KEY,
    project_id UUID REFERENCES buildx_projects(project_id),
    utility_type VARCHAR(50), -- AQUA, POWER, THERMA
    metric_value NUMERIC,
    unit VARCHAR(20),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fce_transactions (
    transaction_id UUID PRIMARY KEY,
    project_id UUID REFERENCES buildx_projects(project_id),
    amount_usd NUMERIC(19, 4) NOT NULL,
    tgst_amount NUMERIC(19, 4),
    green_tax_usd NUMERIC(19, 4),
    status VARCHAR(50) DEFAULT 'PENDING_ESCROW',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_shadow_hash ON shadow_ledger(current_hash);
CREATE INDEX idx_utility_project ON buildx_utility_logs(project_id);
