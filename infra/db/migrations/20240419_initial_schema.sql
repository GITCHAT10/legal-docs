-- AEGIS Tables
CREATE TABLE aegis_users (id UUID PRIMARY KEY, username TEXT, role_id UUID);
CREATE TABLE aegis_roles (id UUID PRIMARY KEY, name TEXT);
CREATE TABLE aegis_practitioner_registry (id UUID PRIMARY KEY, national_id TEXT, name TEXT);
CREATE TABLE aegis_practitioner_licenses (id UUID PRIMARY KEY, practitioner_id UUID, license_no TEXT);

-- SHADOW Tables
CREATE TABLE shadow_logs (id UUID PRIMARY KEY, transaction_id UUID, event_id UUID, data JSONB);
CREATE TABLE shadow_events (id UUID PRIMARY KEY, event_type TEXT, payload JSONB);
CREATE TABLE shadow_hash_chain (id SERIAL PRIMARY KEY, current_hash TEXT, previous_hash TEXT);
CREATE TABLE shadow_signatures (id UUID PRIMARY KEY, entity_id UUID, signature TEXT);

-- ELEONE Tables
CREATE TABLE eleone_policies (id UUID PRIMARY KEY, name TEXT, content TEXT);
CREATE TABLE eleone_policy_versions (id UUID PRIMARY KEY, policy_id UUID, version TEXT);
CREATE TABLE eleone_decisions (id UUID PRIMARY KEY, transaction_id UUID, decision TEXT);

-- EVENT BUS Tables
CREATE TABLE event_bus_messages (id UUID PRIMARY KEY, topic TEXT, payload JSONB, status TEXT);
CREATE TABLE event_delivery_attempts (id UUID PRIMARY KEY, message_id UUID, attempt_count INT);
CREATE TABLE event_dead_letter_queue (id UUID PRIMARY KEY, message_id UUID, reason TEXT);

-- FCE Tables
CREATE TABLE fce_invoices (id UUID PRIMARY KEY, transaction_id UUID, total DECIMAL);
CREATE TABLE fce_invoice_lines (id UUID PRIMARY KEY, invoice_id UUID, description TEXT, amount DECIMAL);
CREATE TABLE fce_payment_splits (id UUID PRIMARY KEY, invoice_id UUID, entity_id UUID, amount DECIMAL);
CREATE TABLE fce_provider_settlements (id UUID PRIMARY KEY, provider_id UUID, amount DECIMAL);

-- LIFELINE Tables
CREATE TABLE lifeline_patients (id UUID PRIMARY KEY, national_id TEXT, name TEXT);
CREATE TABLE lifeline_encounters (id UUID PRIMARY KEY, patient_id UUID, practitioner_id UUID);
CREATE TABLE lifeline_triage_records (id UUID PRIMARY KEY, encounter_id UUID, vital_signs JSONB);
CREATE TABLE lifeline_consultations (id UUID PRIMARY KEY, encounter_id UUID, notes TEXT);
CREATE TABLE lifeline_clinical_notes (id UUID PRIMARY KEY, encounter_id UUID, content TEXT);
CREATE TABLE lifeline_diagnoses (id UUID PRIMARY KEY, encounter_id UUID, diagnosis_code TEXT);
CREATE TABLE lifeline_treatment_plans (id UUID PRIMARY KEY, patient_id UUID, description TEXT);
CREATE TABLE lifeline_case_attachments (id UUID PRIMARY KEY, record_id UUID, file_path TEXT);

-- AASANDHA Tables
CREATE TABLE aasandha_eligibility_checks (id UUID PRIMARY KEY, national_id TEXT, timestamp TIMESTAMP);
CREATE TABLE aasandha_preauthorizations (id UUID PRIMARY KEY, patient_id UUID, amount DECIMAL);
CREATE TABLE aasandha_claims (id UUID PRIMARY KEY, transaction_id UUID, status TEXT);
CREATE TABLE aasandha_claim_lines (id UUID PRIMARY KEY, claim_id UUID, service_code TEXT, amount DECIMAL);
CREATE TABLE aasandha_reimbursements (id UUID PRIMARY KEY, claim_id UUID, amount DECIMAL);

-- PHARMACY Tables
CREATE TABLE pharmacy_medicines (id UUID PRIMARY KEY, name TEXT, drug_code TEXT);
CREATE TABLE pharmacy_medicine_batches (id UUID PRIMARY KEY, medicine_id UUID, batch_no TEXT, expiry_date DATE);
CREATE TABLE pharmacy_prescriptions (id UUID PRIMARY KEY, patient_id UUID, prescriber_id UUID);
CREATE TABLE pharmacy_dispenses (id UUID PRIMARY KEY, prescription_id UUID, dispensed_by UUID);
CREATE TABLE pharmacy_stock_movements (id UUID PRIMARY KEY, medicine_id UUID, quantity INT, type TEXT);

-- DIAGNOSTICS Tables
CREATE TABLE diagnostics_orders (id UUID PRIMARY KEY, patient_id UUID, order_type TEXT);
CREATE TABLE diagnostics_specimens (id UUID PRIMARY KEY, order_id UUID, specimen_type TEXT);
CREATE TABLE diagnostics_results (id UUID PRIMARY KEY, order_id UUID, result_data JSONB);
CREATE TABLE diagnostics_imaging_studies (id UUID PRIMARY KEY, patient_id UUID, modality TEXT);
CREATE TABLE diagnostics_abnormal_flags (id UUID PRIMARY KEY, result_id UUID, flag_level TEXT);

-- FINANCE Tables
CREATE TABLE finance_patient_invoices (id UUID PRIMARY KEY, patient_id UUID, amount DECIMAL);
CREATE TABLE finance_invoice_lines (id UUID PRIMARY KEY, invoice_id UUID, amount DECIMAL);
CREATE TABLE finance_receipts (id UUID PRIMARY KEY, invoice_id UUID, amount DECIMAL);
CREATE TABLE finance_payments (id UUID PRIMARY KEY, invoice_id UUID, status TEXT);
CREATE TABLE finance_refunds (id UUID PRIMARY KEY, payment_id UUID, amount DECIMAL);
CREATE TABLE finance_provider_ledgers (id UUID PRIMARY KEY, provider_id UUID, balance DECIMAL);

-- PAYMENTS Tables
CREATE TABLE payments_transactions (id UUID PRIMARY KEY, amount DECIMAL, status TEXT);
CREATE TABLE payments_callbacks (id UUID PRIMARY KEY, transaction_id UUID, payload JSONB);
CREATE TABLE payments_refunds (id UUID PRIMARY KEY, transaction_id UUID, amount DECIMAL);

-- NOTIFICATIONS Tables
CREATE TABLE notifications_messages (id UUID PRIMARY KEY, recipient_id UUID, content TEXT);
CREATE TABLE notifications_delivery_attempts (id UUID PRIMARY KEY, message_id UUID, status TEXT);
CREATE TABLE notifications_alert_rules (id UUID PRIMARY KEY, name TEXT, criteria JSONB);

-- TELEMEDICINE Tables
CREATE TABLE telemedicine_sessions (id UUID PRIMARY KEY, patient_id UUID, practitioner_id UUID);
CREATE TABLE telemedicine_referrals (id UUID PRIMARY KEY, patient_id UUID, to_specialty TEXT);
CREATE TABLE telemedicine_file_shares (id UUID PRIMARY KEY, session_id UUID, file_path TEXT);

-- INVENTORY Tables
CREATE TABLE inventory_items (id UUID PRIMARY KEY, name TEXT, category TEXT);
CREATE TABLE inventory_stock_levels (id UUID PRIMARY KEY, item_id UUID, quantity INT);
CREATE TABLE inventory_transfer_requests (id UUID PRIMARY KEY, item_id UUID, from_location UUID, to_location UUID);
CREATE TABLE inventory_usage_logs (id UUID PRIMARY KEY, item_id UUID, quantity INT);

-- ANALYTICS Tables
CREATE TABLE analytics_kpi_snapshots (id UUID PRIMARY KEY, metric_name TEXT, value DECIMAL);
CREATE TABLE analytics_wait_time_metrics (id UUID PRIMARY KEY, facility_id UUID, average_wait_time INT);
CREATE TABLE analytics_claim_efficiency_metrics (id UUID PRIMARY KEY, metric_name TEXT, efficiency_score DECIMAL);

-- PUBLIC_HEALTH Tables
CREATE TABLE public_health_case_signals (id UUID PRIMARY KEY, signal_type TEXT, location_id UUID);
CREATE TABLE public_health_clusters (id UUID PRIMARY KEY, signal_type TEXT, radius DECIMAL);
CREATE TABLE public_health_alerts (id UUID PRIMARY KEY, alert_type TEXT, severity TEXT);

-- IDENTITY_BRIDGE Tables
CREATE TABLE identity_bridge_requests (id UUID PRIMARY KEY, request_type TEXT, payload JSONB);
CREATE TABLE identity_bridge_national_id_links (id UUID PRIMARY KEY, national_id TEXT, local_patient_id UUID);
CREATE TABLE identity_bridge_practitioner_sync_logs (id UUID PRIMARY KEY, timestamp TIMESTAMP, status TEXT);
