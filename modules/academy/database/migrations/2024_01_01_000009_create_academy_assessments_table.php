<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('academy_assessments', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('academy_course_id')->index()->constrained('academy_courses');
            $table->string('title');
            $table->integer('max_score');
            $table->timestamps();
            $table->softDeletes();


        });
    }

    public function down(): void
    {
        Schema::dropIfExists('academy_assessments');
    }
};
