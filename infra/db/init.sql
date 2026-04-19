-- PROCUREMENT ORDERS
CREATE TABLE procurement_orders (
    id UUID PRIMARY KEY,
    item VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(15, 2) NOT NULL,
    vendor_id VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SHADOW CHAIN (Audit Ledger)
CREATE TABLE shadow_chain (
    id SERIAL PRIMARY KEY,
    entry_data JSONB NOT NULL,
    previous_hash CHAR(64) NOT NULL,
    current_hash CHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SAL AUDIT LOG
CREATE TABLE sal_audit_log (
    id UUID PRIMARY KEY,
    service VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    payload JSONB,
    timestamp TIMESTAMP NOT NULL
);

-- SVD VERIFICATIONS
CREATE TABLE svd_verifications (
    id UUID PRIMARY KEY,
    item_type VARCHAR(100) NOT NULL,
    confidence DECIMAL(4, 3) NOT NULL,
    rules_passed TEXT[],
    verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CERTIFICATES
CREATE TABLE certificates (
    id UUID PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    issued_to VARCHAR(255) NOT NULL,
    expiry_date DATE,
    metadata JSONB
);

-- EVENT STREAMS
CREATE TABLE event_streams (
    id BIGSERIAL PRIMARY KEY,
    topic VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
