<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('academy_cohorts', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('academy_course_id')->index()->constrained('academy_courses');
            $table->string('name');
            $table->date('start_date');
            $table->date('end_date');
            $table->timestamps();
            $table->softDeletes();


        });
    }

    public function down(): void
    {
        Schema::dropIfExists('academy_cohorts');
    }
};
