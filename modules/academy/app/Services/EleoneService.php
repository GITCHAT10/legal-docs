<?php

namespace Modules\Academy\App\Services;

use Illuminate\Support\Facades\Http;

class EleoneService
{
    public function getDropoutRiskScore($learnerId)
    {
        $response = Http::post('http://mnos-core/v1/mnos/eleone/evaluate', [
            'type' => 'DROPOUT_RISK',
            'entity_id' => $learnerId
        ]);

        return $response->json('score') ?? 0.0;
    }

    public function detectSkillGap($learnerId)
    {
        $response = Http::post('http://mnos-core/v1/mnos/eleone/evaluate', [
            'type' => 'SKILL_GAP',
            'entity_id' => $learnerId
        ]);

        return $response->json('gaps') ?? [];
    }
}
