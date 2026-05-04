-- MIOS: Maldives Import Operating System Database Schema
-- Architecture: N-DEOS Hardened Sovereign Core

-- 1. MASTER SHIPMENT TABLE
CREATE TABLE mios_shipments (
    id UUID PRIMARY KEY,
    customer_id UUID NOT NULL,
    origin_hub_code VARCHAR(10) NOT NULL, -- CN, IN, DXB, TH
    destination_hub_code VARCHAR(10) DEFAULT 'MV',
    status VARCHAR(50) NOT NULL,
    total_actual_cbm DECIMAL(19,4),
    total_actual_weight_kg DECIMAL(19,4),
    is_private_project_cargo BOOLEAN DEFAULT FALSE,
    is_urgent_dispatch BOOLEAN DEFAULT FALSE,
    landed_cost_locked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    shadow_last_event_hash CHAR(64)
);

-- 2. CARGO / LOTS TABLE
CREATE TABLE mios_cargo (
    id UUID PRIMARY KEY,
    shipment_id UUID REFERENCES mios_shipments(id),
    container_id VARCHAR(50), -- Link to a consolidation container
    description TEXT,
    length_cm DECIMAL(10,2),
    width_cm DECIMAL(10,2),
    height_cm DECIMAL(10,2),
    actual_weight_kg DECIMAL(19,4),
    volumetric_weight_kg DECIMAL(19,4),
    chargeable_weight_kg DECIMAL(19,4),
    actual_cbm DECIMAL(19,4),
    cargo_lane VARCHAR(20), -- ORANGE, BLUE, RED, PURPLE, BLACK
    parcel_eligible BOOLEAN,
    qc_status VARCHAR(50),
    photo_proof_ids TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. CONSOLIDATION CONTAINERS
CREATE TABLE mios_containers (
    id UUID PRIMARY KEY,
    container_no VARCHAR(50),
    hub_code VARCHAR(10),
    type VARCHAR(20), -- 20FT, 40HC
    capacity_cbm DECIMAL(10,2),
    current_utilization_cbm DECIMAL(10,2),
    utilization_pct DECIMAL(5,2),
    status VARCHAR(50), -- CONSOLIDATING, READY_AT_85_PERCENT, etc.
    dispatch_reason VARCHAR(50),
    manifest_locked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. SKY FREIGHT GDS (MOVEMENT TRUTH)
CREATE TABLE mios_freight_bookings (
    id UUID PRIMARY KEY,
    shipment_id UUID REFERENCES mios_shipments(id),
    carrier_name VARCHAR(100),
    mode VARCHAR(50), -- SEA_LCL, SEA_FCL, AIR_CARGO, etc.
    booking_ref VARCHAR(100),
    bl_awb_no VARCHAR(100),
    vessel_flight_no VARCHAR(100),
    etd TIMESTAMP WITH TIME ZONE,
    eta TIMESTAMP WITH TIME ZONE,
    freight_status VARCHAR(50),
    freight_cost_usd DECIMAL(19,4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. SKY CLEARING (CUSTOMS & PORT)
CREATE TABLE mios_clearing_records (
    id UUID PRIMARY KEY,
    shipment_id UUID REFERENCES mios_shipments(id),
    invoice_no VARCHAR(100),
    invoice_total_usd DECIMAL(19,4),
    invoice_verified BOOLEAN DEFAULT FALSE,
    hs_code VARCHAR(20),
    hs_code_confirmed BOOLEAN DEFAULT FALSE,
    declaration_no VARCHAR(100),
    assessment_no VARCHAR(100),
    customs_payment_receipt_no VARCHAR(100),
    customs_payment_matched BOOLEAN DEFAULT FALSE,
    port_release_status VARCHAR(50),
    port_release_verified BOOLEAN DEFAULT FALSE,
    orca_validation_results JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. MIOS FX (RATE CONTROL)
CREATE TABLE mios_fx_rates (
    id UUID PRIMARY KEY,
    shipment_id UUID REFERENCES mios_shipments(id),
    source_currency CHAR(3),
    target_currency CHAR(3),
    rate_type VARCHAR(50), -- QUOTE_RATE, CUSTOMS_RATE, etc.
    fx_rate DECIMAL(19,6),
    is_locked BOOLEAN DEFAULT FALSE,
    locked_at TIMESTAMP WITH TIME ZONE,
    shadow_event_id CHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. FCE LEDGER (FINANCIAL TRUTH)
CREATE TABLE mios_fce_ledger (
    id UUID PRIMARY KEY,
    shipment_id UUID REFERENCES mios_shipments(id),
    category VARCHAR(50), -- GOVERNMENT_PASS_THROUGH, PLATFORM_REVENUE, etc.
    line_item_name VARCHAR(255),
    amount_mvr DECIMAL(19,4),
    amount_original DECIMAL(19,4),
    original_currency CHAR(3),
    receipt_id VARCHAR(100),
    is_verified BOOLEAN DEFAULT FALSE,
    status VARCHAR(50), -- ESTIMATE, ACTUAL, SETTLED
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. ASSET HANDOFF (CHAIN OF CUSTODY)
CREATE TABLE mios_asset_handoffs (
    id UUID PRIMARY KEY,
    shipment_id UUID REFERENCES mios_shipments(id),
    handoff_type VARCHAR(50), -- ORIGIN_RECEIPT, FINAL_DELIVERY, etc.
    sender_id UUID,
    receiver_id UUID,
    location_name VARCHAR(255),
    gps_coords POINT,
    condition_status VARCHAR(50),
    damage_flag BOOLEAN DEFAULT FALSE,
    package_count_received INT,
    receiver_signature_hash CHAR(64),
    photo_proof_ids TEXT[],
    status VARCHAR(50), -- VERIFIED, DISPUTED
    shadow_event_id CHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 9. MIOS SHADOW AUDIT (Local reference to Global Shadow)
CREATE TABLE mios_audit_events (
    id UUID PRIMARY KEY,
    shipment_id UUID REFERENCES mios_shipments(id),
    event_type VARCHAR(100),
    actor_id UUID,
    portal VARCHAR(50),
    old_state_hash CHAR(64),
    new_state_hash CHAR(64),
    shadow_hash CHAR(64), -- SHA256 linkage
    parent_hash CHAR(64), -- Chain linkage
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
