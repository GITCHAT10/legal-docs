-- UT PPMC Initial Schema

-- Identity & Roles
CREATE TABLE ut_aegis_partner_profiles (
    identity_id UUID PRIMARY KEY,
    partner_type VARCHAR(50), -- HOTEL, RESORT, DMC, etc.
    verified BOOLEAN DEFAULT FALSE
);

-- Vendors
CREATE TABLE ut_vendors (
    vendor_id UUID PRIMARY KEY,
    business_name VARCHAR(255),
    kyc_status VARCHAR(50),
    payout_profile_id UUID
);

CREATE TABLE ut_vendor_documents (
    doc_id UUID PRIMARY KEY,
    vendor_id UUID REFERENCES ut_vendors(vendor_id),
    doc_type VARCHAR(50),
    expiry_date DATE,
    status VARCHAR(50)
);

-- Assets (Vessels/Vehicles)
CREATE TABLE ut_assets (
    asset_id UUID PRIMARY KEY,
    vendor_id UUID REFERENCES ut_vendors(vendor_id),
    template_id VARCHAR(100),
    asset_type VARCHAR(50), -- SPEEDBOAT, YACHT, BUS, etc.
    capacity INT,
    status VARCHAR(50)
);

-- Routes & Schedules
CREATE TABLE ut_routes (
    route_id UUID PRIMARY KEY,
    origin_node VARCHAR(100),
    destination_node VARCHAR(100),
    transport_mode VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE ut_route_schedules (
    schedule_id UUID PRIMARY KEY,
    route_id UUID REFERENCES ut_routes(route_id),
    departure_time TIME,
    arrival_time TIME,
    days_of_week INT[]
);

-- Journeys & Bookings
CREATE TABLE ut_journeys (
    journey_id UUID PRIMARY KEY,
    trace_id UUID UNIQUE NOT NULL,
    customer_id UUID,
    status VARCHAR(50),
    created_at TIMESTAMP WITH TIME_ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ut_journey_legs (
    leg_id UUID PRIMARY KEY,
    journey_id UUID REFERENCES ut_journeys(journey_id),
    route_id UUID REFERENCES ut_routes(route_id),
    asset_id UUID REFERENCES ut_assets(asset_id),
    departure_time TIMESTAMP WITH TIME_ZONE,
    arrival_time TIMESTAMP WITH TIME_ZONE,
    leg_order INT,
    status VARCHAR(50)
);

CREATE TABLE ut_bookings (
    booking_id UUID PRIMARY KEY,
    journey_id UUID REFERENCES ut_journeys(journey_id),
    trace_id UUID NOT NULL,
    pricing_quote_id UUID,
    status VARCHAR(50)
);

CREATE TABLE ut_manifests (
    manifest_id UUID PRIMARY KEY,
    leg_id UUID REFERENCES ut_journey_legs(leg_id),
    asset_id UUID REFERENCES ut_assets(asset_id),
    lock_status BOOLEAN DEFAULT FALSE
);

-- Finance
CREATE TABLE ut_fce_quotes (
    quote_id UUID PRIMARY KEY,
    trace_id UUID NOT NULL,
    base_amount DECIMAL(19,4),
    tax_amount DECIMAL(19,4),
    service_charge DECIMAL(19,4),
    esg_csr_fee DECIMAL(19,4),
    total_amount DECIMAL(19,4),
    is_locked BOOLEAN DEFAULT FALSE
);

CREATE TABLE ut_fce_ledgers (
    ledger_entry_id UUID PRIMARY KEY,
    quote_id UUID REFERENCES ut_fce_quotes(quote_id),
    ledger_type VARCHAR(50),
    amount DECIMAL(19,4),
    status VARCHAR(50)
);

-- Shadow & Audit
CREATE TABLE ut_shadow_events (
    event_id UUID PRIMARY KEY,
    trace_id UUID NOT NULL,
    event_type VARCHAR(100),
    actor_id UUID,
    payload JSONB,
    event_hash VARCHAR(64),
    previous_hash VARCHAR(64),
    created_at TIMESTAMP WITH TIME_ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Fuel & ESG
CREATE TABLE ut_fuel_logs (
    log_id UUID PRIMARY KEY,
    asset_id UUID REFERENCES ut_assets(asset_id),
    leg_id UUID REFERENCES ut_journey_legs(leg_id),
    fuel_amount DECIMAL(10,2),
    logged_at TIMESTAMP WITH TIME_ZONE DEFAULT CURRENT_TIMESTAMP
);
