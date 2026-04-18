<?php

return [
    'detectors' => [
        App\Services\Detectors\Implementations\ValueShaveDetector::class,
        App\Services\Detectors\Implementations\TaxMismatchDetector::class,
    ],
];
