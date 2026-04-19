<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('academy_fee_plans', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('academy_institution_id')->index()->constrained('academy_institutions');
            $table->string('name');
            $table->decimal('total_amount', 15, 2);
            $table->timestamps();
            $table->softDeletes();


        });
    }

    public function down(): void
    {
        Schema::dropIfExists('academy_fee_plans');
    }
};
