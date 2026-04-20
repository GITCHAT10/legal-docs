<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Concerns\HasUuids;

class EnforcementAction extends Model
{
    use HasUuids;

    protected $guarded = [];

    protected $casts = [
        'payload' => 'array',
    ];
}
