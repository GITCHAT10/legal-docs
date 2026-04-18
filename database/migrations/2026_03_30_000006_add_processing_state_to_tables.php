<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        // Add processing state to shadow_entries (if not already present)
        Schema::table('shadow_entries', function (Blueprint $table) {
            if (!Schema::hasColumn('shadow_entries', 'is_processing')) {
                $table->boolean('is_processing')->default(false)->after('idempotency_key')->index();
            }
            if (!Schema::hasColumn('shadow_entries', 'processed_at')) {
                $table->timestamp('processed_at')->nullable()->after('is_processing')->index();
            }
        });

        // Add processing state to revenue_anomalies for async enforcement
        Schema::table('revenue_anomalies', function (Blueprint $table) {
            if (!Schema::hasColumn('revenue_anomalies', 'is_processing')) {
                $table->boolean('is_processing')->default(false)->after('status')->index();
            }
            if (!Schema::hasColumn('revenue_anomalies', 'processed_at')) {
                $table->timestamp('processed_at')->nullable()->after('is_processing')->index();
            }
        });

        // Add index for processing queue polling
        Schema::table('shadow_entries', function (Blueprint $table) {
            $table->index(['is_processing', 'processed_at'], 'idx_processing_queue_poll');
        });
    }

    public function down(): void
    {
        Schema::table('shadow_entries', function (Blueprint $table) {
            $table->dropIndex('idx_processing_queue_poll');
            $table->dropColumn(['is_processing', 'processed_at']);
        });

        Schema::table('revenue_anomalies', function (Blueprint $table) {
            $table->dropColumn(['is_processing', 'processed_at']);
        });
    }
};
