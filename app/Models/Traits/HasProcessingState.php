<?php

namespace App\Models\Traits;

trait HasProcessingState
{
    public function scopeUnprocessed($query)
    {
        return $query->whereNull('processed_at')->where('is_processing', false);
    }

    public function markAsProcessing()
    {
        $this->update(['is_processing' => true]);
    }

    public function markAsProcessed()
    {
        $this->update([
            'is_processing' => false,
            'processed_at' => now(),
        ]);
    }
}
