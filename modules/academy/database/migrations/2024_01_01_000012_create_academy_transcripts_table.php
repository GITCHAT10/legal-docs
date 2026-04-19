<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('academy_transcripts', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('academy_learner_id')->index()->constrained('academy_learners');
            $table->json('records');
            $table->timestamps();
            $table->softDeletes();


        });
    }

    public function down(): void
    {
        Schema::dropIfExists('academy_transcripts');
    }
};
