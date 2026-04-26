-- iMOXON N-DEOS Database Schema (Consolidated RC1)
-- Migration: RC1 persistence layer (2026-04-26)
-- Added: clearance_declarations, pca_vault, shadow_audit_ref FKs
-- Preserved: backward compatibility with in-memory event schema

CREATE TABLE aegis_identities (
    id UUID PRIMARY KEY,
    did VARCHAR(100) UNIQUE,
    role VARCHAR(50),
    national_id_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE imoxon_suppliers (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    type VARCHAR(50), -- GLOBAL, LOCAL
    kyc_status VARCHAR(50), -- PENDING, VERIFIED, REJECTED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE imoxon_catalog (
    id UUID PRIMARY KEY,
    supplier_id UUID REFERENCES imoxon_suppliers(id),
    name VARCHAR(255),
    base_price DECIMAL(19,4),
    landed_cost DECIMAL(19,4),
    status VARCHAR(50), -- PENDING_APPROVAL, APPROVED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE imoxon_orders (
    id UUID PRIMARY KEY,
    buyer_id UUID,
    items JSONB,
    pricing JSONB,
    status VARCHAR(50), -- CREATED, APPROVED, DISPATCHED, DELIVERED, INVOICED, SETTLED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE imoxon_installments (
    id UUID PRIMARY KEY,
    order_id UUID REFERENCES imoxon_orders(id),
    plan_id VARCHAR(50) UNIQUE,
    schedule JSONB,
    status VARCHAR(50), -- ACTIVE, COMPLETED, DEFAULTED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE logistics_shipments (
    id VARCHAR(50) PRIMARY KEY,
    supplier_id UUID REFERENCES imoxon_suppliers(id),
    order_id UUID REFERENCES imoxon_orders(id),
    origin VARCHAR(100),
    destination VARCHAR(100),
    status VARCHAR(30), -- CREATED, PRECHECK_OK, DISPATCHED, ARRIVED_MALDIVES, CLEARED, RECEIVED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE clearance_declarations (
    declaration_id VARCHAR(32) PRIMARY KEY,
    shipment_id VARCHAR(50) REFERENCES logistics_shipments(id),
    current_state VARCHAR(30) NOT NULL, -- CREATED, PRECHECK_OK, DECLARED, ASSESSED, PAID, RELEASED, MPL_PENDING, GATE_OUT, SKYGODOWN_INTAKE
    state_history JSONB NOT NULL,
    mpl_gate_pass VARCHAR(32),
    pca_vault_id VARCHAR(32),
    shadow_audit_ref VARCHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pca_vault (
    vault_id VARCHAR(32) PRIMARY KEY,
    declaration_id VARCHAR(32) REFERENCES clearance_declarations(declaration_id),
    status VARCHAR(30), -- BUILDING, READY, SEALED
    documents JSONB, -- List of doc types and hashes
    retention_until TIMESTAMP, -- 6-year legal requirement
    sealed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE shadow_ledger (
    entry_id UUID PRIMARY KEY,
    action_type VARCHAR(100),
    actor_id VARCHAR(100),
    payload JSONB,
    data JSONB, -- Test compatibility
    previous_hash VARCHAR(64),
    hash VARCHAR(64),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
