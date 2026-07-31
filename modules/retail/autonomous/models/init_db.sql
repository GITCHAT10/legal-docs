-- MARS A-RETAIL Hardened Database Schema
-- For PostgreSQL (MNOS Native)

CREATE TABLE retail_stores (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    property_id VARCHAR,
    name VARCHAR NOT NULL,
    mode VARCHAR DEFAULT 'ASSISTED_AUTONOMOUS',
    hardware_profile_json JSONB,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE retail_hardware_nodes (
    id UUID PRIMARY KEY,
    store_id UUID REFERENCES retail_stores(id),
    node_type VARCHAR,
    node_identifier VARCHAR UNIQUE,
    zone VARCHAR,
    status VARCHAR,
    trust_score NUMERIC(5,4) DEFAULT 1.0,
    config_json JSONB,
    last_seen_at TIMESTAMP WITH TIME ZONE,
    last_heartbeat_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE retail_sessions (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    aegis_user_id UUID NOT NULL,
    store_id VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'OPEN',
    auth_type VARCHAR,
    confidence_score NUMERIC(5,4),
    entry_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    exit_time TIMESTAMP WITH TIME ZONE,
    trace_id UUID,
    idempotency_key VARCHAR UNIQUE,
    settlement_id UUID,
    receipt_id VARCHAR,
    anomaly_flags JSONB,
    evidence_bundle JSONB,
    reviewer_id UUID,
    review_reason VARCHAR,
    parent_session_id UUID,
    shadow_hash TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE retail_session_events (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES retail_sessions(id),
    tenant_id UUID NOT NULL,
    event_type VARCHAR,
    source VARCHAR,
    hardware_id VARCHAR,
    product_id VARCHAR,
    qty NUMERIC(10,2),
    confidence NUMERIC(5,4),
    trust_score_at_event NUMERIC(5,4),
    is_duplicate BOOLEAN DEFAULT FALSE,
    payload_json JSONB,
    trace_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE retail_session_cart_items (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES retail_sessions(id),
    product_id VARCHAR NOT NULL,
    qty NUMERIC(10,2) NOT NULL,
    unit_price NUMERIC(10,2) NOT NULL,
    subtotal NUMERIC(10,2) NOT NULL,
    price_snapshot JSONB,
    confidence_score NUMERIC(5,4),
    anomaly_flags JSONB,
    status VARCHAR DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
