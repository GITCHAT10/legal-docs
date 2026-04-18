<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use App\Models\Traits\HasProcessingState;
use App\Models\Traits\HasFingerprintDedup;
use Illuminate\Database\Eloquent\Concerns\HasUuids;

class RevenueAnomaly extends Model
{
    use HasUuids, HasProcessingState, HasFingerprintDedup;

    protected $guarded = [];

    protected $casts = [
        'scoring_breakdown' => 'array',
        'diff' => 'array',
        'context' => 'array',
        'detection_metadata' => 'array',
        'detected_at' => 'datetime',
        'reviewed_at' => 'datetime',
        'resolved_at' => 'datetime',
        'processed_at' => 'datetime',
        'is_processing' => 'boolean',
        'enforcement_triggered' => 'boolean',
    ];

    public function generateFingerprint(): string
    {
        $components = [
            $this->aggregate_type,
            $this->aggregate_id,
            $this->type,
            json_encode($this->diff ?? []),
        ];

        return hash('sha256', implode('|', $components));
    }

    public function evidence()
    {
        return $this->belongsTo(EvidenceRecord::class, 'evidence_record_id');
    }
}
