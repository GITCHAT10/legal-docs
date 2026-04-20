<?php

namespace App\Services\Evidence;

use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Validator;
use App\Models\ShadowEntry;
use App\Models\RevenueAnomaly;

class EvidenceBuilder
{
    /**
     * JSON Schema for evidence validation.
     *
     * @var array
     */
    protected array $schema;

    public function __construct(array $schema = [])
    {
        // CRITICAL FIX #6: Load structured evidence schema
        $this->schema = $schema ?: config('evidence.schemas.default', $this->getDefaultSchema());
    }

    /**
     * Build structured evidence record.
     *
     * @param ShadowEntry $shadowEntry
     * @param RevenueAnomaly $anomaly
     * @param array $liveData
     * @return array
     */
    public function build(ShadowEntry $shadowEntry, RevenueAnomaly $anomaly, array $liveData = []): array
    {
        // === SHADOW: Original captured event ===
        $shadow = [
            'event_id' => $shadowEntry->id,
            'event_type' => $shadowEntry->event_type,
            'aggregate_id' => $shadowEntry->aggregate_id,
            'aggregate_type' => $shadowEntry->aggregate_type,
            'version' => $shadowEntry->version,
            'payload' => $shadowEntry->payload,
            'metadata' => $shadowEntry->metadata,
            'occurred_at' => $shadowEntry->occurred_at->toISOString(),
            'captured_at' => $shadowEntry->captured_at->toISOString(),
            // CRITICAL FIX #5: Include origin tracking
            'origin' => [
                'source_system' => $shadowEntry->source_system,
                'device_id' => $shadowEntry->device_id,
                'user_agent' => $shadowEntry->user_agent,
                'ip_address' => $shadowEntry->ip_address,
            ],
        ];

        // === LIVE: Current system state (for comparison) ===
        $live = [
            'snapshot_taken_at' => now()->toISOString(),
            'data' => $liveData ?: $this->fetchLiveData($shadowEntry),
            'source' => $this->determineLiveDataSource($shadowEntry),
        ];

        // === DIFF: What changed (anomaly details) ===
        $diff = $this->generateDiff($shadowEntry->payload, $live['data'], $anomaly->diff);

        // === TIMELINE: Event sequence reconstruction ===
        $timeline = $this->reconstructTimeline($shadowEntry, $anomaly);

        // === SYSTEM CONTEXT: Environmental factors ===
        $systemContext = [
            'detection_timestamp' => $anomaly->detected_at->toISOString(),
            'detector_class' => $anomaly->detector_class,
            'detector_config' => $anomaly->detection_metadata['detector_config'] ?? [],
            'thresholds_used' => $anomaly->detection_metadata['thresholds'] ?? [],
            'processing_node' => gethostname(),
            'queue_latency_ms' => $anomaly->detection_metadata['queue_latency_ms'] ?? null,
        ];

        // === RULE TRIGGERED: Which rule fired ===
        $ruleTriggered = [
            'rule_id' => $anomaly->detection_metadata['rule_id'] ?? null,
            'rule_name' => $anomaly->detection_metadata['rule_name'] ?? null,
            'rule_version' => $anomaly->detection_metadata['rule_version'] ?? null,
            'condition_evaluated' => $anomaly->detection_metadata['condition'] ?? null,
        ];

        // === ASSEMBLE STRUCTURED EVIDENCE ===
        $evidence = [
            'shadow' => $shadow,
            'live' => $live,
            'diff' => $diff,
            'timeline' => $timeline,
            'system_context' => $systemContext,
            'rule_triggered' => $ruleTriggered,
            // Metadata for audit trail
            'meta' => [
                'evidence_version' => '1.0',
                'schema_version' => $this->schema['$schema'] ?? 'default',
                'generated_at' => now()->toISOString(),
                'generated_by' => 'EvidenceBuilder::build',
            ],
        ];

        // === VALIDATE AGAINST SCHEMA ===
        $validation = Validator::make(
            $evidence,
            $this->getLaravelValidationRules($this->schema)
        );

        if ($validation->fails()) {
            Log::error('Evidence schema validation failed', [
                'errors' => $validation->errors()->toArray(),
                'evidence_sample' => array_slice($evidence, 0, 3, true),
            ]);
            // Still return evidence but flag for review
            $evidence['meta']['validation_warnings'] = $validation->errors()->toArray();
        }

        return $evidence;
    }

    /**
     * Get default evidence schema (CRITICAL FIX #6).
     *
     * @return array
     */
    protected function getDefaultSchema(): array
    {
        return [
            '$schema' => 'https://json-schema.org/draft/2020-12/schema',
            '$id' => 'https://fce.sios-rms.mv/schemas/evidence-v1.json',
            'title' => 'Financial Control Engine Evidence Record',
            'type' => 'object',
            'required' => ['shadow', 'live', 'diff', 'timeline', 'system_context', 'rule_triggered', 'meta'],
            'properties' => [
                'shadow' => [
                    'type' => 'object',
                    'required' => ['event_id', 'event_type', 'aggregate_id', 'payload', 'occurred_at'],
                    'properties' => [
                        'origin' => [
                            'type' => 'object',
                            'properties' => [
                                'source_system' => ['type' => 'string'],
                                'device_id' => ['type' => 'string'],
                                'ip_address' => ['type' => 'string', 'format' => 'ipv4'],
                            ],
                        ],
                    ],
                ],
                'live' => ['type' => 'object'],
                'diff' => ['type' => 'object'],
                'timeline' => [
                    'type' => 'array',
                    'items' => [
                        'type' => 'object',
                        'required' => ['timestamp', 'event', 'source'],
                    ],
                ],
                'system_context' => ['type' => 'object'],
                'rule_triggered' => ['type' => 'object'],
                'meta' => [
                    'type' => 'object',
                    'required' => ['evidence_version', 'generated_at'],
                ],
            ],
        ];
    }

    /**
     * Convert JSON Schema to Laravel validation rules.
     *
     * @param array $schema
     * @return array
     */
    protected function getLaravelValidationRules(array $schema): array
    {
        // Simplified conversion for demo; in production use full JSON Schema validator
        return [
            'shadow' => 'required|array',
            'shadow.event_id' => 'required',
            'live' => 'required|array',
            'diff' => 'required|array',
            'timeline' => 'required|array',
            'system_context' => 'required|array',
            'rule_triggered' => 'required|array',
            'meta' => 'required|array',
            'meta.evidence_version' => 'required|string',
            'meta.generated_at' => 'required',
        ];
    }

    /**
     * Fetch live data for comparison.
     */
    protected function fetchLiveData(ShadowEntry $shadowEntry): array
    {
        return match ($shadowEntry->aggregate_type) {
            'Folio' => $this->fetchFolioLiveData($shadowEntry->aggregate_id),
            'Booking' => $this->fetchBookingLiveData($shadowEntry->aggregate_id),
            'Payment' => $this->fetchPaymentLiveData($shadowEntry->aggregate_id),
            default => [],
        };
    }

    protected function fetchFolioLiveData($id) { return []; }
    protected function fetchBookingLiveData($id) { return []; }
    protected function fetchPaymentLiveData($id) { return []; }

    protected function determineLiveDataSource($entry) { return 'external_api'; }

    /**
     * Generate structured diff between shadow and live.
     */
    protected function generateDiff(array $shadowPayload, array $liveData, ?array $anomalyDiff): array
    {
        if (!empty($anomalyDiff)) {
            return $anomalyDiff;
        }

        $diff = [];
        $allKeys = array_unique(array_merge(
            array_keys($shadowPayload),
            array_keys($liveData)
        ));

        foreach ($allKeys as $key) {
            $old = $shadowPayload[$key] ?? null;
            $new = $liveData[$key] ?? null;

            if ($old !== $new) {
                $diff[$key] = [
                    'old' => $old,
                    'new' => $new,
                    'changed_at' => $liveData['updated_at'] ?? null,
                ];
            }
        }

        return $diff;
    }

    /**
     * Reconstruct event timeline for investigation.
     */
    protected function reconstructTimeline(ShadowEntry $shadowEntry, RevenueAnomaly $anomaly): array
    {
        $timeline = [];

        $timeline[] = [
            'timestamp' => $shadowEntry->occurred_at->toISOString(),
            'event' => 'event_captured',
            'source' => 'shadow_ledger',
            'data' => [
                'event_id' => $shadowEntry->id,
                'event_type' => $shadowEntry->event_type,
            ],
        ];

        $timeline[] = [
            'timestamp' => $anomaly->detected_at->toISOString(),
            'event' => 'anomaly_detected',
            'source' => 'detector_engine',
            'data' => [
                'anomaly_id' => $anomaly->id,
                'anomaly_type' => $anomaly->type,
                'risk_score' => $anomaly->risk_score,
            ],
        ];

        $relatedEvents = ShadowEntry::where('aggregate_type', $shadowEntry->aggregate_type)
            ->where('aggregate_id', $shadowEntry->aggregate_id)
            ->where('id', '!=', $shadowEntry->id)
            ->orderBy('occurred_at')
            ->limit(5)
            ->get();

        foreach ($relatedEvents as $event) {
            $timeline[] = [
                'timestamp' => $event->occurred_at->toISOString(),
                'event' => 'related_event',
                'source' => 'shadow_ledger',
                'data' => [
                    'event_id' => $event->id,
                    'event_type' => $event->event_type,
                ],
            ];
        }

        usort($timeline, fn($a, $b) =>
            strtotime($a['timestamp']) <=> strtotime($b['timestamp'])
        );

        return $timeline;
    }
}
