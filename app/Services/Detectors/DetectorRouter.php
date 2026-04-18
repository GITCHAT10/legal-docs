<?php

namespace App\Services\Detectors;

use Illuminate\Support\Collection;
use Illuminate\Contracts\Container\Container;
use App\Events\FinancialEvent;
use LogicException;

class DetectorRouter
{
    /**
     * Registered detector instances.
     *
     * @var Collection<BaseDetector>
     */
    protected Collection $detectors;

    /**
     * Container for dependency injection.
     */
    protected Container $container;

    public function __construct(Container $container)
    {
        $this->container = $container;
        $this->detectors = collect();
    }

    /**
     * Register a detector instance.
     *
     * @param BaseDetector $detector
     * @return self
     */
    public function register(BaseDetector $detector): self
    {
        $this->detectors->push($detector);
        return $this;
    }

    /**
     * Register detectors from configuration.
     *
     * @param array $config
     * @return self
     */
    public function registerFromConfig(array $config): self
    {
        foreach ($config['detectors'] ?? [] as $detectorClass) {
            // CRITICAL FIX #3: Modular, plug-and-play detector registration
            $detector = $this->container->make($detectorClass);

            if (!$detector instanceof BaseDetector) {
                throw new LogicException("Detector {$detectorClass} must extend BaseDetector");
            }

            $this->register($detector);
        }

        return $this;
    }

    /**
     * Route an event to the appropriate detector(s).
     *
     * @param FinancialEvent $event
     * @return Collection<DetectorResult>
     */
    public function detect(FinancialEvent $event): Collection
    {
        // CRITICAL FIX #3: Replace match($eventType) with plugin architecture
        return $this->detectors
            ->filter(fn(BaseDetector $detector) => $detector->isEnabled() && $detector->supports($event->getType()))
            ->map(fn(BaseDetector $detector) => $detector->analyze($event))
            ->filter(fn(?DetectorResult $result) => $result !== null);
    }

    /**
     * Route an event to the appropriate detector(s) and return results with metadata.
     */
    public function detectWithMetadata(FinancialEvent $event): Collection
    {
        return $this->detectors
            ->filter(fn(BaseDetector $detector) => $detector->isEnabled() && $detector->supports($event->getType()))
            ->map(fn(BaseDetector $detector) => [
                'detector_class' => get_class($detector),
                'result' => $detector->analyze($event)
            ])
            ->filter(fn($data) => $data['result'] !== null);
    }

    /**
     * Get all registered detectors (for admin UI).
     *
     * @return array
     */
    public function getRegisteredDetectors(): array
    {
        return $this->detectors->map(fn(BaseDetector $detector) => [
            'class' => get_class($detector),
            'event_types' => $detector->getSupportedEventTypes(),
            'config' => $detector->getConfig(),
            'enabled' => $detector->isEnabled(),
        ])->toArray();
    }

    /**
     * Enable/disable a detector at runtime.
     *
     * @param string $detectorClass
     * @param bool $enabled
     * @return bool
     */
    public function setDetectorEnabled(string $detectorClass, bool $enabled): bool
    {
        $detector = $this->detectors->first(
            fn(BaseDetector $d) => get_class($d) === $detectorClass
        );

        if (!$detector) {
            return false;
        }

        $detector->setEnabled($enabled);
        return true;
    }
}
