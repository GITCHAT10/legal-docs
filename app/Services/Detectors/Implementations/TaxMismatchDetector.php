<?php

namespace App\Services\Detectors\Implementations;

use App\Services\Detectors\BaseDetector;
use App\Events\FinancialEvent;
use App\Services\Detectors\DetectorResult;

class TaxMismatchDetector extends BaseDetector
{
    protected array $supportedEventTypes = ['FOLIO_POSTED'];

    public function analyze(FinancialEvent $event): ?DetectorResult
    {
        $payload = $event->getPayload();
        $base = $payload['base_amount'] ?? 0;
        $serviceCharge = $payload['service_charge'] ?? 0;
        $tgst = $payload['tgst'] ?? 0;

        $expectedServiceCharge = round($base * 0.10, 2);
        $expectedTgst = round(($base + $expectedServiceCharge) * 0.17, 2);

        if ($serviceCharge != $expectedServiceCharge || $tgst != $expectedTgst) {
            return new DetectorResult(
                type: 'TAX_MISMATCH',
                diff: [
                    'expected_tgst' => $expectedTgst,
                    'actual_tgst' => $tgst,
                    'expected_sc' => $expectedServiceCharge,
                    'actual_sc' => $serviceCharge
                ],
                confidence: 1.0,
                metadata: [
                    'field' => 'tax_calculation',
                    'financial_impact' => abs($tgst - $expectedTgst) + abs($serviceCharge - $expectedServiceCharge)
                ]
            );
        }

        return null;
    }
}
