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
            $table->string('type', 100)->index();
            $table->string('detector_class', 255);
            $table->string('aggregate_type', 100);
            // ISSUE 3 FIX: aggregate_id must be string, not uuid
            $table->string('aggregate_id', 100)->index();

            // === CRITICAL FIX #7: ANOMALY DEDUPLICATION ===
            $table->string('fingerprint', 64)->unique()->index();

            // === CRITICAL FIX #4: SEPARATED SCORING (NOT SINGLE anomaly_score) ===
            $table->integer('severity_score')->unsigned()->default(0);
            $table->integer('confidence_score')->unsigned()->default(0);
            $table->integer('risk_score')->unsigned()->default(0);
            $table->json('scoring_breakdown')->nullable();

            // === ANOMALY DETAILS ===
            $table->text('description')->nullable();
            $table->json('diff')->nullable();
            $table->json('context')->nullable();

            // === CRITICAL FIX #6: STRUCTURED EVIDENCE REFERENCE ===
            $table->uuid('evidence_record_id')->nullable();

            // === STATE & LIFECYCLE ===
            $table->string('status', 20)->default('detected')->index();
            $table->string('priority', 20)->default('medium')->index();
            $table->timestamp('detected_at')->useCurrent();
            $table->timestamp('reviewed_at')->nullable();
            $table->timestamp('resolved_at')->nullable();
            $table->uuid('reviewed_by')->nullable();
            $table->text('resolution_notes')->nullable();

            // === ENFORCEMENT TRACKING ===
            $table->boolean('enforcement_triggered')->default(false);
            $table->uuid('enforcement_action_id')->nullable();

            // === AUDIT TRAIL ===
            $table->json('detection_metadata')->nullable();
            $table->string('source_event_id')->nullable();

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
