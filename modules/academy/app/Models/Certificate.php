<?php

namespace Modules\Academy\App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;
use Modules\Academy\App\Models\Traits\HasMNOSIdentity;
use Modules\Academy\App\Models\Traits\EmitsMNOSEvents;
use Modules\Academy\App\Models\Traits\ShadowSyncable;

class Certificate extends Model
{
    use HasMNOSIdentity, EmitsMNOSEvents, ShadowSyncable, SoftDeletes;

    protected $table = 'academy_certificates';
    protected $guarded = ['id', 'created_at', 'updated_at', 'deleted_at'];
}
