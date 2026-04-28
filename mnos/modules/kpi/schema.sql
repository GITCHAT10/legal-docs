-- schema.sql
CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    trigger_type VARCHAR(50),
    segment VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS email_events (
    trace_id VARCHAR(50) PRIMARY KEY,
    campaign_id VARCHAR(50) REFERENCES campaigns(campaign_id),
    recipient VARCHAR(255),
    event_type VARCHAR(20), -- sent, opened, clicked, converted
    event_ts TIMESTAMPTZ DEFAULT NOW(),
    pricing_id VARCHAR(50),
    tax_type VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS bookings (
    booking_id VARCHAR(50) PRIMARY KEY,
    trace_id VARCHAR(50) UNIQUE REFERENCES email_events(trace_id),
    gross_amount DECIMAL(12,2) NOT NULL,
    net_amount DECIMAL(12,2) NOT NULL,
    margin_amount DECIMAL(12,2) NOT NULL,
    commission_amount DECIMAL(12,2) NOT NULL,
    tax_amount DECIMAL(12,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'confirmed',
    booked_ts TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS outreach_tracker (
    email VARCHAR(255) PRIMARY KEY,
    company VARCHAR(255),
    region VARCHAR(50),
    country VARCHAR(50),
    agent_type VARCHAR(50),
    priority_tier VARCHAR(10),
    contact_role VARCHAR(50),
    status VARCHAR(50) DEFAULT 'not-contacted',
    trigger_segment VARCHAR(50),
    last_contact TIMESTAMPTZ,
    notes TEXT
);

-- Index for fast attribution joins
CREATE INDEX IF NOT EXISTS idx_events_campaign_ts ON email_events(campaign_id, event_ts);
CREATE INDEX IF NOT EXISTS idx_bookings_trace ON bookings(trace_id);
