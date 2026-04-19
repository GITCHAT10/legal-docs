<?php

namespace Modules\Academy\App\Models\Traits;

use Illuminate\Support\Str;

trait HasMNOSIdentity
{
    protected static function bootHasMNOSIdentity()
    {
        static::creating(function ($model) {
            if (empty($model->id)) {
                $model->id = (string) Str::uuid7();
            }
        });
    }

    public function getIncrementing()
    {
        return false;
    }

    public function getKeyType()
    {
        return 'string';
    }
}
