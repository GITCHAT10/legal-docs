<?php

namespace Modules\Academy\App\Actions;

use Modules\Academy\App\Models\Certificate;

class IssueCertificate
{
    public function execute(array $data)
    {
        $certificate = Certificate::create($data);

        // Ensure critical data is synced to SHADOW
        $certificate->syncToShadow();

        return $certificate;
    }
}
