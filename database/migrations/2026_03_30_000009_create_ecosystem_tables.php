<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('demands', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->string('source');
            $table->string('user_type');
            $table->string('priority');
            $table->string('status')->default('pending');
            $table->json('payload');
            $table->timestamps();
        });

        Schema::create('decisions', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->uuid('demand_id');
            $table->string('fulfillment_mode');
            $table->string('logistics_mode');
            $table->string('assigned_node');
            $table->decimal('price', 15, 2);
            $table->timestamp('eta')->nullable();
            $table->timestamps();
        });

        Schema::create('shipments', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->uuid('decision_id');
            $table->string('warehouse_id');
            $table->string('status')->default('ready');
            $table->string('mode');
            $table->decimal('weight', 10, 2);
            $table->timestamps();
        });

        Schema::create('flights', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->uuid('shipment_id');
            $table->timestamp('departure');
            $table->timestamp('arrival');
            $table->string('status')->default('assigned');
            $table->timestamps();
        });

        Schema::create('financial_ledger', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->uuid('reference_id'); // e.g. folio_id or demand_id
            $table->decimal('base', 15, 2);
            $table->decimal('service_charge', 15, 2);
            $table->decimal('tgst', 15, 2);
            $table->decimal('green_tax', 15, 2)->default(0);
            $table->decimal('total', 15, 2);
            $table->string('status')->default('posted');
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('financial_ledger');
        Schema::dropIfExists('flights');
        Schema::dropIfExists('shipments');
        Schema::dropIfExists('decisions');
        Schema::dropIfExists('demands');
    }
};
