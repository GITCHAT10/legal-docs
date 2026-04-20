<?php

namespace App\Services\Detectors\Implementations;

use App\Services\Detectors\BaseDetector;
use App\Events\FinancialEvent;
use App\Services\Detectors\DetectorResult;

class ValueShaveDetector extends BaseDetector
{
    protected array $supportedEventTypes = ['booking.created'];

    public function analyze(FinancialEvent $event): ?DetectorResult
    {
        $payload = $event->getPayload();
        $roomRate = $payload['room_rate'] ?? 0;
        $prevRate = $payload['previous_rate'] ?? 0;

        if ($prevRate > 0 && $roomRate < $prevRate) {
            return new DetectorResult(
                type: 'VALUE_SHAVE',
                diff: ['old' => $prevRate, 'new' => $roomRate],
                confidence: 0.9,
                metadata: [
                    'field' => 'room_rate',
                    'financial_impact' => $prevRate - $roomRate
                ]
            );
        }

        return null;
    }
}
