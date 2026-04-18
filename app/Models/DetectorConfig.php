<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Concerns\HasUuids;

class DetectorConfig extends Model
{
    use HasUuids;

    protected $guarded = [];

    protected $casts = [
        'config' => 'array',
        'enabled' => 'boolean',
    ];
}
