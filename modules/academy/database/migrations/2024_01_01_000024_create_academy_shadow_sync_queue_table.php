<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('academy_shadow_sync_queue', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->string('entity_type')->index();
            $table->uuid('entity_id')->index();
            $table->string('hash');
            $table->timestamp('synced_at')->nullable()->index();
            $table->timestamps();
            $table->softDeletes();


        });
    }

    public function down(): void
    {
        Schema::dropIfExists('academy_shadow_sync_queue');
    }
};
