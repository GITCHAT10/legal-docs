<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('academy_refunds', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('academy_payment_id')->index()->constrained('academy_payments');
            $table->decimal('amount', 15, 2);
            $table->string('reason');
            $table->timestamps();
            $table->softDeletes();


        });
    }

    public function down(): void
    {
        Schema::dropIfExists('academy_refunds');
    }
};
