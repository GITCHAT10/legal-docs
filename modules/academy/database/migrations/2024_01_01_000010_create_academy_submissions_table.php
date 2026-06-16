<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('academy_submissions', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('academy_assessment_id')->index()->constrained('academy_assessments');
            $table->foreignUuid('academy_learner_id')->index()->constrained('academy_learners');
            $table->json('content');
            $table->timestamps();
            $table->softDeletes();


        });
    }

    public function down(): void
    {
        Schema::dropIfExists('academy_submissions');
    }
};
