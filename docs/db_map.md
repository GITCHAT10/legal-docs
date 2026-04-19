# MNOS LIFELINE Database Table Map

## 1. aegis_db
- **users**: id, user_uuid, username, password_hash, status, created_at, updated_at
- **roles**: id, role_code, role_name
- **user_roles**: id, user_id, role_id, facility_id
- **practitioners**: id, practitioner_uuid, user_id, full_name, license_no, specialty_code, mmdc_status, facility_id, signature_key_ref, is_active
- **patients_identity**: id, patient_uuid, national_id, e_faas_ref, biometric_hash_ref, full_name, date_of_birth, sex, mobile_no, status
- **facilities**: id, facility_uuid, facility_code, facility_name, atoll_code, island_code, status
- **sessions**: id, session_uuid, user_id, access_token_hash, refresh_token_hash, ip_address, device_fingerprint, expires_at

## 2. shadow_db
- **audit_events**: id, event_uuid, actor_type, actor_id, facility_id, module_name, entity_type, entity_id, action_code, event_payload_json, created_at
- **hash_chain**: id, event_id, previous_hash, current_hash, algorithm, chain_position, stamped_at
- **evidence_links**: id, event_id, evidence_type, evidence_ref, checksum
- **divergence_events**: id, divergence_uuid, consultation_id, ai_suggestion_id, doctor_id, divergence_reason_code, divergence_note, created_at
- **access_lookbacks**: id, requestor_id, event_id, purpose_code, requested_at

## 3. eleone_db
- **policies**: id, policy_code, policy_name, policy_version, policy_scope, status
- **policy_rules**: id, policy_id, rule_code, rule_expression, severity, action_on_fail
- **policy_evaluations**: id, evaluation_uuid, policy_code, subject_type, subject_id, input_payload_json, result_status, fail_reason, evaluated_at
- **prescriber_validations**: id, validation_uuid, practitioner_id, license_no, action_type, registry_status, result_status, validated_at
- **claim_validations**: id, validation_uuid, claim_id, rule_set_version, result_status, fail_reason, validated_at

## 4. fce_db
- **price_catalog**: id, item_code, item_name, item_type, base_mvr, effective_from, effective_to
- **claim_calculations**: id, calculation_uuid, claim_id, patient_id, covered_amount_mvr, copay_amount_mvr, provider_payable_mvr, calc_version, created_at
- **settlement_calculations**: id, settlement_uuid, facility_id, claim_batch_id, total_claimed_mvr, total_approved_mvr, total_payable_mvr, created_at

## 5. lifeline_db
- **patients**: id, patient_uuid, identity_ref, mrn, facility_id, primary_language, blood_group, allergies_summary, created_at
- **patient_contacts**: id, patient_id, contact_type, name, phone, relationship
- **encounters**: id, encounter_uuid, patient_id, facility_id, encounter_type, arrival_mode, status, opened_at, closed_at
- **triage_records**: id, encounter_id, nurse_id, chief_complaint, temperature, pulse_rate, bp_systolic, bp_diastolic, spo2, urgency_level, recorded_at
- **consultations**: id, consultation_uuid, encounter_id, practitioner_id, consultation_status, presenting_complaint, clinical_notes, diagnosis_summary, started_at, ended_at
- **consultation_diagnoses**: id, consultation_id, icd10_code, diagnosis_type, is_primary
- **care_plans**: id, care_plan_uuid, consultation_id, plan_text, followup_date, status
- **prescriptions**: id, prescription_uuid, consultation_id, practitioner_id, prescription_status, signed_at, signature_ref
- **prescription_items**: id, prescription_id, item_code, item_name, dosage, frequency, duration_days, quantity, route
- **clinical_documents**: id, document_uuid, patient_id, consultation_id, document_type, content_ref, checksum, created_at
- **ai_suggestions**: id, suggestion_uuid, consultation_id, model_name, suggestion_type, suggestion_payload_json, confidence_score, created_at
- **doctor_approvals**: id, approval_uuid, suggestion_id, practitioner_id, decision, approval_note, approved_at

## 6. aasandha_db
- **eligibility_checks**: id, eligibility_uuid, patient_id, external_member_ref, eligibility_status, response_payload_json, checked_at
- **preauth_requests**: id, preauth_uuid, consultation_id, facility_id, patient_id, claim_basis_code, requested_amount_mvr, status, requested_at
- **claims**: id, claim_uuid, preauth_id, consultation_id, facility_id, patient_id, claim_status, submitted_at
- **claim_items**: id, claim_id, item_code, item_type, qty, unit_price_mvr, total_price_mvr
- **claim_responses**: id, claim_id, external_claim_ref, response_status, response_payload_json, responded_at
- **claim_batches**: id, batch_uuid, facility_id, batch_status, submitted_count, total_amount_mvr, created_at
- **settlement_records**: id, settlement_uuid, batch_id, facility_id, settlement_status, settled_amount_mvr, settled_at
- **fraud_flags**: id, flag_uuid, claim_id, risk_type, risk_score, flag_status, created_at

## 7. pharmacy_db
- **formulary_items**: id, item_code, generic_name, brand_name, strength, dosage_form, atc_code, controlled_flag
- **drug_interactions**: id, interaction_uuid, item_code_a, item_code_b, severity, interaction_note
- **dispense_records**: id, dispense_uuid, prescription_id, patient_id, facility_id, dispensed_by, dispense_status, dispensed_at
- **dispense_items**: id, dispense_id, formulary_item_id, quantity, batch_no, expiry_date
- **pharmacy_stock**: id, facility_id, item_code, on_hand_qty, reserved_qty, reorder_level, updated_at
- **reorder_suggestions**: id, suggestion_uuid, facility_id, item_code, suggested_qty, reason_code, created_at

## 8. diagnostics_db
- **diagnostic_orders**: id, order_uuid, consultation_id, patient_id, practitioner_id, order_type, status, ordered_at
- **lab_orders**: id, diagnostic_order_id, lab_test_code, specimen_type, priority
- **radiology_orders**: id, diagnostic_order_id, modality_code, body_part, contrast_flag
- **diagnostic_results**: id, result_uuid, diagnostic_order_id, result_type, abnormal_flag, result_status, resulted_at
- **lab_results**: id, diagnostic_result_id, analyte_code, analyte_name, result_value, unit, reference_range
- **radiology_reports**: id, diagnostic_result_id, report_text, dicom_study_uid, impression
- **dicom_links**: id, diagnostic_result_id, pacs_ref, study_uid, series_uid, image_count

## 9. finance_db
- **invoices**: id, invoice_uuid, patient_id, encounter_id, facility_id, invoice_status, total_mvr, issued_at
- **invoice_items**: id, invoice_id, item_code, item_type, qty, unit_price_mvr, total_mvr
- **copay_records**: id, copay_uuid, invoice_id, patient_id, payable_mvr, paid_mvr, status
- **cashier_transactions**: id, transaction_uuid, invoice_id, payment_method, amount_mvr, external_payment_ref, transaction_status, created_at
- **provider_settlements**: id, settlement_uuid, facility_id, claim_batch_id, amount_mvr, settlement_status, settled_at
- **refunds**: id, refund_uuid, transaction_id, amount_mvr, reason, refund_status, refunded_at

## 10. telemedicine_db
- **tele_sessions**: id, session_uuid, patient_id, origin_facility_id, specialist_facility_id, session_status, started_at, ended_at
- **tele_referrals**: id, referral_uuid, consultation_id, referred_by, referred_to, reason_text, urgency_level, created_at
- **tele_attachments**: id, attachment_uuid, session_id, attachment_type, file_ref, checksum
- **tele_notes**: id, note_uuid, session_id, author_id, note_text, created_at

## 11. public_health_db
- **anonymized_cases**: id, case_uuid, source_facility_id, atoll_code, island_code, age_band, sex, syndrome_code, diagnosis_code, event_date
- **cluster_detections**: id, cluster_uuid, syndrome_code, region_code, case_count, detection_window, risk_level, detected_at
- **public_alerts**: id, alert_uuid, alert_type, region_code, alert_message, alert_status, created_at
- **trend_snapshots**: id, snapshot_uuid, metric_code, region_code, metric_value, snapshot_date
- **climate_links**: id, link_uuid, region_code, external_source, signal_type, signal_value, linked_at

## 12. inventory_db
- **consumable_items**: id, item_code, item_name, category_code, unit_of_measure
- **facility_inventory**: id, facility_id, item_code, on_hand_qty, reorder_level, updated_at
- **inventory_transfers**: id, transfer_uuid, from_facility_id, to_facility_id, transfer_status, requested_at, completed_at
- **inventory_transfer_items**: id, transfer_id, item_code, quantity
- **vendors**: id, vendor_uuid, vendor_name, contact_name, contact_phone, status
- **forecast_runs**: id, forecast_uuid, facility_id, run_date, model_name, output_ref

## 13. payments_db
- **payment_requests**: id, payment_uuid, invoice_id, payer_type, amount_mvr, channel_code, request_status, requested_at
- **payment_responses**: id, payment_request_id, external_ref, response_code, response_payload_json, responded_at
- **receipts**: id, receipt_uuid, payment_request_id, receipt_no, amount_mvr, issued_at
- **refund_requests**: id, refund_uuid, payment_request_id, amount_mvr, reason, refund_status, requested_at

## 14. analytics_db
- **ops_dashboard_daily**: id, facility_id, dashboard_date, patients_seen, avg_wait_minutes, consultations_completed, claims_submitted
- **clinical_dashboard_daily**: id, facility_id, dashboard_date, top_diagnosis_code, abnormal_results_count, ai_divergence_count
- **finance_dashboard_daily**: id, facility_id, dashboard_date, invoiced_mvr, copay_collected_mvr, claim_payable_mvr
- **public_health_dashboard_daily**: id, region_code, dashboard_date, syndrome_alert_count, cluster_count, outbreak_risk_score
