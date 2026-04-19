<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('academy_attendance', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('academy_enrollment_id')->index()->constrained('academy_enrollments');
            $table->date('date')->index();
            $table->boolean('is_present');
            $table->timestamps();
            $table->softDeletes();


        });
    }

    public function down(): void
    {
        Schema::dropIfExists('academy_attendance');
    }
};
