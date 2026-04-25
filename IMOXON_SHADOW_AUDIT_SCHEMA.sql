CREATE TABLE shadow_commerce_events (
    block_id SERIAL PRIMARY KEY,
    event_type VARCHAR(100),
    actor_id UUID,
    device_id UUID,
    payload JSONB,
    previous_hash CHAR(64),
    current_hash CHAR(64),
    timestamp TIMESTAMP
);
