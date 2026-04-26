-- iMOXON N-DEOS Database Schema (Consolidated)

CREATE TABLE aegis_identities (
    id UUID PRIMARY KEY,
    did VARCHAR(100) UNIQUE,
    role VARCHAR(50),
    national_id_verified BOOLEAN DEFAULT FALSE
);

CREATE TABLE imoxon_suppliers (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    type VARCHAR(50),
    kyc_status VARCHAR(50)
);

CREATE TABLE imoxon_catalog (
    id UUID PRIMARY KEY,
    supplier_id UUID,
    name VARCHAR(255),
    base_price DECIMAL(19,4),
    landed_cost DECIMAL(19,4),
    status VARCHAR(50)
);

CREATE TABLE imoxon_orders (
    id UUID PRIMARY KEY,
    buyer_id UUID,
    items JSONB,
    pricing JSONB,
    status VARCHAR(50),
    created_at TIMESTAMP
);

CREATE TABLE imoxon_installments (
    id UUID PRIMARY KEY,
    order_id UUID,
    plan_id VARCHAR(50),
    schedule JSONB,
    status VARCHAR(50)
);

CREATE TABLE exchange_assets (
    id UUID PRIMARY KEY,
    owner_did VARCHAR(100),
    description TEXT,
    price DECIMAL(19,4),
    status VARCHAR(50)
);

CREATE TABLE shadow_ledger (
    entry_id UUID PRIMARY KEY,
    action_type VARCHAR(100),
    actor_id VARCHAR(100),
    payload JSONB,
    previous_hash VARCHAR(64),
    timestamp TIMESTAMP
);
