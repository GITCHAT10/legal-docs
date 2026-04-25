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
    status VARCHAR(50)
);
