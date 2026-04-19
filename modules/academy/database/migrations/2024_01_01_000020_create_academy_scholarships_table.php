<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('academy_scholarships', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->foreignUuid('academy_learner_id')->index()->constrained('academy_learners');
            $table->decimal('amount', 15, 2);
            $table->string('type')->index();
            $table->timestamps();
            $table->softDeletes();


        });
    }

    public function down(): void
    {
        Schema::dropIfExists('academy_scholarships');
    }
};
