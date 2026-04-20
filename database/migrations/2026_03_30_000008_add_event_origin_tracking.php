<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        // Add event origin tracking to shadow_entries
        Schema::table('shadow_entries', function (Blueprint $table) {
            if (!Schema::hasColumn('shadow_entries', 'source_system')) {
                $table->string('source_system', 50)->nullable()->after('metadata')->index();
            }
            if (!Schema::hasColumn('shadow_entries', 'device_id')) {
                $table->string('device_id', 100)->nullable()->after('source_system')->index();
            }
            if (!Schema::hasColumn('shadow_entries', 'user_agent')) {
                $table->string('user_agent')->nullable()->after('device_id');
            }
            if (!Schema::hasColumn('shadow_entries', 'ip_address')) {
                $table->ipAddress('ip_address')->nullable()->after('user_agent');
            }
        });

        // Add indexes for fraud detection queries
        Schema::table('shadow_entries', function (Blueprint $table) {
            $table->index(['source_system', 'occurred_at'], 'idx_source_timeline');
            $table->index(['device_id', 'event_type'], 'idx_device_event_pattern');
            $table->index(['ip_address', 'aggregate_id'], 'idx_ip_aggregate_fraud');
        });
    }

    public function down(): void
    {
        Schema::table('shadow_entries', function (Blueprint $table) {
            if (Schema::hasColumn('shadow_entries', 'source_system')) {
                $table->dropIndex('idx_source_timeline');
                $table->dropColumn('source_system');
            }
            if (Schema::hasColumn('shadow_entries', 'device_id')) {
                $table->dropIndex('idx_device_event_pattern');
                $table->dropColumn('device_id');
            }
            if (Schema::hasColumn('shadow_entries', 'ip_address')) {
                $table->dropIndex('idx_ip_aggregate_fraud');
                $table->dropColumn('ip_address');
            }
            if (Schema::hasColumn('shadow_entries', 'user_agent')) {
                $table->dropColumn('user_agent');
            }
        });
    }
};
