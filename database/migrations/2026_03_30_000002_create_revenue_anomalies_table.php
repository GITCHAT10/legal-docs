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
            $table->string('type', 100)->index();
            $table->string('detector_class', 255);
            $table->string('aggregate_type', 100);
            $table->string('aggregate_id', 100)->index();
            $table->string('fingerprint', 64)->unique()->index();
            $table->integer('severity_score')->unsigned()->default(0);
            $table->integer('confidence_score')->unsigned()->default(0);
            $table->integer('risk_score')->unsigned()->default(0);
            $table->json('scoring_breakdown')->nullable();
            $table->text('description')->nullable();
            $table->json('diff')->nullable();
            $table->json('context')->nullable();
            $table->uuid('evidence_record_id')->nullable();
            $table->string('status', 20)->default('detected')->index();
            $table->string('priority', 20)->default('medium')->index();
            $table->timestamp('detected_at')->useCurrent();
            $table->timestamp('reviewed_at')->nullable();
            $table->timestamp('resolved_at')->nullable();
            $table->uuid('reviewed_by')->nullable();
            $table->text('resolution_notes')->nullable();
            $table->boolean('enforcement_triggered')->default(false);
            $table->uuid('enforcement_action_id')->nullable();
            $table->json('detection_metadata')->nullable();
            $table->string('source_event_id')->nullable();
            $table->timestamps();

            $table->index(['status', 'priority', 'detected_at'], 'idx_anomaly_triage_queue');
            $table->index(['aggregate_type', 'aggregate_id'], 'idx_anomaly_by_entity');
            $table->index(['risk_score', 'detected_at'], 'idx_high_risk_recent');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('revenue_anomalies');
    }
};
