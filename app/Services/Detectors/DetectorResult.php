<?php

namespace App\Services\Detectors;

class DetectorResult
{
    public function __construct(
        public string $type,
        public array $diff,
        public float $confidence = 1.0,
        public array $metadata = []
    ) {}
}
