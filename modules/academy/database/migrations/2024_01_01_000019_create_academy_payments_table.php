<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('academy_payments', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('academy_invoice_id')->index()->constrained('academy_invoices');
            $table->decimal('amount', 15, 2);
            $table->string('method')->index();
            $table->timestamps();
            $table->softDeletes();


        });
    }

    public function down(): void
    {
        Schema::dropIfExists('academy_payments');
    }
};
