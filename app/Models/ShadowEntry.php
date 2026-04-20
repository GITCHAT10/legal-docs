<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use App\Models\Traits\HasImmutableAudit;
use App\Models\Traits\HasProcessingState;
use Illuminate\Database\Eloquent\Concerns\HasUuids;

class ShadowEntry extends Model
{
    use HasUuids, HasImmutableAudit, HasProcessingState;

    protected $guarded = [];

    protected $casts = [
        'payload' => 'array',
        'metadata' => 'array',
        'occurred_at' => 'datetime',
        'captured_at' => 'datetime',
        'processed_at' => 'datetime',
        'is_processing' => 'boolean',
    ];
}
