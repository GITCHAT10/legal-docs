<?php

namespace Modules\Academy\App\Models\Traits;

use Modules\Academy\App\Services\MNOS\MnosClient;

trait EmitsMNOSEvents
{
    protected static function bootEmitsMNOSEvents()
    {
        static::creating(function ($model) {
            // Flow step 1: ELEONE decision request before DB write
            MnosClient::eleone('PERMISSION_CHECK', $model->id ?? 'pending', [
                'entity_type' => class_basename($model),
                'action' => 'CREATE'
            ]);
        });

        static::created(function ($model) {
            $model->mnosSync('CREATE');
        });

        static::updated(function ($model) {
            $model->mnosSync('UPDATE');
        });

        static::deleted(function ($model) {
            $model->mnosSync('DELETE');
        });
    }

    public function mnosSync($action)
    {
        $payload = $this->toArray();

        // 1. Emit Event via SDK
        MnosClient::event('academy.' . strtolower(class_basename($this)) . '.' . strtolower($action), $payload);

        // 2. Write to SHADOW (Final Authority Gate) via SDK
        MnosClient::shadow(class_basename($this), $this->id, $payload, $action);
    }
}
