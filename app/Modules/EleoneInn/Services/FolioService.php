<?php

namespace App\Modules\EleoneInn\Services;

class FolioService
{
    /**
     * Maldives Billing Logic (MIRA Compliant)
     */
    public function calculate(float $base)
    {
        $serviceCharge = $base * 0.10;
        $subtotal = $base + $serviceCharge;
        $tgst = $subtotal * 0.17; // Updated TGST rate

        return [
            'base' => $base,
            'service_charge' => $serviceCharge,
            'tgst' => $tgst,
            'total' => $subtotal + $tgst
        ];
    }
}
