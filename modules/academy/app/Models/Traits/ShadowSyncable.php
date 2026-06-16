<?php

namespace Modules\Academy\App\Models\Traits;

use Modules\Academy\App\Services\MNOS\MnosClient;

trait ShadowSyncable
{
    public function syncToShadow()
    {
        return MnosClient::shadow(
            class_basename($this),
            $this->id,
            $this->toArray(),
            'SYNC'
        );
    }
}
