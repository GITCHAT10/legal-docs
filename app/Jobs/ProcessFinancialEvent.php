<?php

namespace App\Jobs;

use App\Models\ShadowEntry;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;

class ProcessFinancialEvent implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public function __construct(protected ShadowEntry $entry) {}

    public function handle()
    {
        // Processing logic
        $this->entry->markAsProcessed();
    }
}
