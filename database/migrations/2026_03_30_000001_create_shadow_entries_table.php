<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;
use Illuminate\Support\Facades\DB;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('shadow_entries', function (Blueprint $table) {
            $table->uuid('id')->primary();

            // === CORE EVENT DATA ===
            $table->string('event_type', 100)->index();
            $table->string('aggregate_id', 100)->index();
            $table->string('aggregate_type', 100);
            $table->integer('version')->unsigned();

            // === EVENT PAYLOAD (IMMUTABLE) ===
            $table->json('payload');
            $table->json('metadata')->nullable();

            // === CRITICAL FIX #5: EVENT ORIGIN TRACKING ===
            $table->string('source_system', 50)->nullable()->index();
            $table->string('device_id', 100)->nullable()->index();
            $table->string('user_agent')->nullable();
            $table->ipAddress('ip_address')->nullable();

            // === CRITICAL FIX #1: REPLAY PROTECTION ===
            $table->string('idempotency_key', 100)->unique();
            $table->timestamp('processed_at')->nullable()->index();

            // === CRITICAL FIX #2: PROCESSING LOCK ===
            $table->boolean('is_processing')->default(false)->index();

            // === AUDIT & IMMUTABILITY ===
            $table->string('signature', 128);
            $table->timestamp('occurred_at');
            $table->timestamp('captured_at')->useCurrent();
            $table->string('captured_by', 100)->default('system');

            // === SOFT DELETE FOR COMPLIANCE (NOT HARD DELETE) ===
            $table->timestamp('deleted_at')->nullable();

            $table->timestamps();

            // === INDEXES FOR PERFORMANCE ===
            $table->index(['aggregate_type', 'aggregate_id', 'version'], 'idx_aggregate_lookup');
            $table->index(['event_type', 'occurred_at'], 'idx_event_type_timeline');
            $table->index(['processed_at', 'is_processing'], 'idx_processing_queue');
        });

        if (DB::getDriverName() === 'pgsql') {
            DB::statement("
                CREATE OR REPLACE FUNCTION prevent_shadow_entry_modification()
                RETURNS TRIGGER AS \$\$
                BEGIN
                    IF TG_OP = 'UPDATE' THEN
                        -- Strictly prevent modification of core data fields
                        IF NEW.payload IS DISTINCT FROM OLD.payload
                           OR NEW.event_type IS DISTINCT FROM OLD.event_type
                           OR NEW.aggregate_id IS DISTINCT FROM OLD.aggregate_id
                           OR NEW.aggregate_type IS DISTINCT FROM OLD.aggregate_type
                           OR NEW.occurred_at IS DISTINCT FROM OLD.occurred_at
                           OR NEW.signature IS DISTINCT FROM OLD.signature
                           OR NEW.idempotency_key IS DISTINCT FROM OLD.idempotency_key THEN
                            RAISE EXCEPTION 'Core fields of Shadow entries are immutable.';
                        END IF;

                        -- Only allow updates to lifecycle and system fields
                        IF NEW.deleted_at IS DISTINCT FROM OLD.deleted_at
                           OR NEW.updated_at IS DISTINCT FROM OLD.updated_at
                           OR NEW.is_processing IS DISTINCT FROM OLD.is_processing
                           OR NEW.processed_at IS DISTINCT FROM OLD.processed_at THEN
                            RETURN NEW;
                        END IF;

                        RETURN OLD;
                    ELSIF TG_OP = 'DELETE' THEN
                        RAISE EXCEPTION 'Shadow entries cannot be deleted. Use redaction via deleted_at.';
                    END IF;
                    RETURN NEW;
                END;
                \$\$ LANGUAGE plpgsql;
            ");

            DB::statement("
                CREATE TRIGGER trg_shadow_entry_immutable
                BEFORE UPDATE OR DELETE ON shadow_entries
                FOR EACH ROW EXECUTE FUNCTION prevent_shadow_entry_modification();
            ");
        }
    }

    public function down(): void
    {
        if (DB::getDriverName() === 'pgsql') {
            DB::statement('DROP TRIGGER IF EXISTS trg_shadow_entry_immutable ON shadow_entries');
            DB::statement('DROP FUNCTION IF EXISTS prevent_shadow_entry_modification()');
        }
        Schema::dropIfExists('shadow_entries');
    }
};
