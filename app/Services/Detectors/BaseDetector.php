<?php

namespace App\Services\Detectors;

use App\Events\FinancialEvent;
use Illuminate\Support\Facades\Log;

abstract class BaseDetector
{
    /**
     * Event types this detector supports.
     *
     * @var array<string>
     */
    protected array $supportedEventTypes = [];

    /**
     * Detector configuration.
     *
     * @var array
     */
    protected array $config = [];

    /**
     * Whether this detector is enabled.
     *
     * @var bool
     */
    protected bool $enabled = true;

    /**
     * Check if this detector supports the given event type.
     *
     * @param string $eventType
     * @return bool
     */
    public function supports(string $eventType): bool
    {
        return in_array($eventType, $this->supportedEventTypes, true);
    }

    /**
     * Get supported event types.
     *
     * @return array<string>
     */
    public function getSupportedEventTypes(): array
    {
        return $this->supportedEventTypes;
    }

    /**
     * Analyze an event for anomalies.
     *
     * @param FinancialEvent $event
     * @return DetectorResult|null
     */
    abstract public function analyze(FinancialEvent $event): ?DetectorResult;

    /**
     * Get detector configuration.
     *
     * @return array
     */
    public function getConfig(): array
    {
        return $this->config;
    }

    /**
     * Update detector configuration at runtime.
     *
     * @param array $config
     * @return self
     */
    public function setConfig(array $config): self
    {
        $this->config = array_merge($this->config, $config);
        return $this;
    }

    /**
     * Check if detector is enabled.
     *
     * @return bool
     */
    public function isEnabled(): bool
    {
        return $this->enabled;
    }

    /**
     * Enable/disable detector.
     *
     * @param bool $enabled
     * @return self
     */
    public function setEnabled(bool $enabled): self
    {
        $this->enabled = $enabled;
        Log::info("Detector " . static::class . " " . ($enabled ? 'enabled' : 'disabled'));
        return $this;
    }

    /**
     * Helper: Calculate anomaly fingerprint for deduplication.
     *
     * @param FinancialEvent $event
     * @param string $anomalyType
     * @param array $diff
     * @return string
     */
    protected function generateFingerprint(FinancialEvent $event, string $anomalyType, array $diff): string
    {
        // CRITICAL FIX #7: Consistent fingerprint for deduplication
        $components = [
            $event->getAggregateType(),
            $event->getAggregateId(),
            $anomalyType,
            // Sort diff keys for consistent hashing
            json_encode($diff, JSON_FORCE_OBJECT | JSON_PRESERVE_ZERO_FRACTION | JSON_UNESCAPED_SLASHES),
        ];

        return hash('sha256', implode('|', $components));
    }
}
