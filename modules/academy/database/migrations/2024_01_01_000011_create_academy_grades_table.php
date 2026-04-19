<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('academy_grades', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('academy_submission_id')->index()->constrained('academy_submissions');
            $table->decimal('score', 8, 2);
            $table->text('feedback')->nullable();
            $table->timestamps();
            $table->softDeletes();


        });
    }

    public function down(): void
    {
        Schema::dropIfExists('academy_grades');
    }
};
