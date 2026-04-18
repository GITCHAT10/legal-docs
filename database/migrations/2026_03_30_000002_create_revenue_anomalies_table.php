<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('revenue_anomalies', function (Blueprint $table) {
            $table->uuid('id')->primary();

            // === ANOMALY IDENTIFICATION ===
            $table->string('type', 100)->index(); // "VALUE_SHAVE", "PHANTOM_BOOKING", etc.
            $table->string('detector_class', 255); // FQCN of detector that found this
            $table->string('aggregate_type', 100); // "Folio", "Booking", etc.
            $table->uuid('aggregate_id'); // Reference to the affected entity

            // === CRITICAL FIX #7: ANOMALY DEDUPLICATION ===
            $table->string('fingerprint', 64)->unique()->index(); // SHA256 hash for dedup
            // fingerprint = hash('sha256', aggregate_type + aggregate_id + type + key_diff_fields)

            // === CRITICAL FIX #4: SEPARATED SCORING (NOT SINGLE anomaly_score) ===
            $table->integer('severity_score')->unsigned()->default(0); // 0-100: Business impact
            $table->integer('confidence_score')->unsigned()->default(0); // 0-100: Detection certainty
            $table->integer('risk_score')->unsigned()->default(0); // 0-100: Composite risk (calculated)
            $table->json('scoring_breakdown')->nullable(); // Detailed scoring components

            // === ANOMALY DETAILS ===
            $table->text('description')->nullable(); // Human-readable explanation
            $table->json('diff')->nullable(); // What changed: {old_value, new_value, field}
            $table->json('context')->nullable(); // Additional context for investigation

            // === CRITICAL FIX #6: STRUCTURED EVIDENCE REFERENCE ===
            $table->uuid('evidence_record_id')->nullable(); // FK to evidence_records
            // Evidence contains: shadow vs live comparison, timeline, system_context, rule_triggered

            // === STATE & LIFECYCLE ===
            $table->string('status', 20)->default('detected')->index(); // detected, reviewing, resolved, false_positive
            $table->string('priority', 20)->default('medium')->index(); // low, medium, high, critical
            $table->timestamp('detected_at')->useCurrent();
            $table->timestamp('reviewed_at')->nullable();
            $table->timestamp('resolved_at')->nullable();
            $table->uuid('reviewed_by')->nullable(); // User who triaged this
            $table->text('resolution_notes')->nullable(); // Why it was resolved a certain way

            // === ENFORCEMENT TRACKING ===
            $table->boolean('enforcement_triggered')->default(false);
            $table->uuid('enforcement_action_id')->nullable(); // FK to enforcement_actions

            // === AUDIT TRAIL ===
            $table->json('detection_metadata')->nullable(); // Detector runtime info, thresholds used
            $table->string('source_event_id')->nullable(); // Original shadow_entry.id that triggered this

            $table->timestamps();

            // === INDEXES ===
            $table->index(['status', 'priority', 'detected_at'], 'idx_anomaly_triage_queue');
            $table->index(['aggregate_type', 'aggregate_id'], 'idx_anomaly_by_entity');
            $table->index(['risk_score', 'detected_at'], 'idx_high_risk_recent');

            // === FOREIGN KEYS ===
            $table->foreign('evidence_record_id')
                  ->references('id')->on('evidence_records')
                  ->nullOnDelete();
            $table->foreign('enforcement_action_id')
                  ->references('id')->on('enforcement_actions')
                  ->nullOnDelete();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('revenue_anomalies');
    }
};
