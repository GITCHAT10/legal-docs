<?php

namespace App\Services\Scoring;

use Illuminate\Support\Facades\Log;

class AnomalyScorer
{
    /**
     * Default scoring weights.
     *
     * @var array
     */
    protected array $defaultWeights = [
        'severity' => 0.40,
        'confidence' => 0.35,
        'business_impact' => 0.25,
    ];

    public function __construct(array $weights = [])
    {
        $this->defaultWeights = array_merge($this->defaultWeights, $weights);
    }

    /**
     * CRITICAL FIX #4: Calculate separated scores (not single anomaly_score)
     *
     * @param array $anomalyData
     * @param array $context
     * @return array{severity_score: int, confidence_score: int, risk_score: int, breakdown: array}
     */
    public function calculateScores(array $anomalyData, array $context = []): array
    {
        // === SEVERITY SCORE: Business impact assessment ===
        $severityScore = $this->calculateSeverityScore($anomalyData, $context);

        // === CONFIDENCE SCORE: Detection certainty ===
        $confidenceScore = $this->calculateConfidenceScore($anomalyData, $context);

        // === RISK SCORE: Composite of severity + confidence + business context ===
        $riskScore = $this->calculateRiskScore($severityScore, $confidenceScore, $anomalyData, $context);

        // === BREAKDOWN: For audit trail and UI transparency ===
        $breakdown = [
            'severity' => [
                'score' => $severityScore,
                'factors' => $this->getSeverityFactors($anomalyData, $context),
            ],
            'confidence' => [
                'score' => $confidenceScore,
                'factors' => $this->getConfidenceFactors($anomalyData, $context),
            ],
            'risk' => [
                'score' => $riskScore,
                'weights_used' => $this->defaultWeights,
                'calculation' => "({$severityScore} × 0.40) + ({$confidenceScore} × 0.35) + (business_impact × 0.25)",
            ],
        ];

        return [
            'severity_score' => $severityScore,
            'confidence_score' => $confidenceScore,
            'risk_score' => $riskScore,
            'breakdown' => $breakdown,
        ];
    }

    /**
     * Calculate severity score (0-100): Business impact.
     */
    protected function calculateSeverityScore(array $anomalyData, array $context): int
    {
        $score = 0;

        // Factor 1: Financial magnitude
        if (isset($anomalyData['financial_impact'])) {
            $impact = $anomalyData['financial_impact'];
            if ($impact >= 10000) $score += 40;
            elseif ($impact >= 1000) $score += 25;
            elseif ($impact >= 100) $score += 10;
        }

        // Factor 2: Affected entity type
        $entityType = $anomalyData['aggregate_type'] ?? '';
        if ($entityType === 'Folio') $score += 20; // High-value entity
        elseif ($entityType === 'Booking') $score += 10;

        // Factor 3: Anomaly type severity mapping
        $severityMap = config('fce.severity_map', [
            'VALUE_SHAVE' => 30,
            'PHANTOM_BOOKING' => 25,
            'TIMING_ANOMALY' => 15,
            'THRESHOLD_BREACH' => 20,
        ]);
        $anomalyType = $anomalyData['type'] ?? '';
        $score += $severityMap[$anomalyType] ?? 10;

        return min(100, $score);
    }

    /**
     * Calculate confidence score (0-100): Detection certainty.
     */
    protected function calculateConfidenceScore(array $anomalyData, array $context): int
    {
        $score = 50; // Base confidence

        // Factor 1: Data completeness
        $requiredFields = ['old_value', 'new_value', 'field', 'timestamp'];
        $presentFields = 0;
        foreach($requiredFields as $f) {
            if (isset($anomalyData[$f])) $presentFields++;
        }
        $score += ($presentFields / count($requiredFields)) * 20;

        // Factor 2: Detector confidence (if provided)
        if (isset($anomalyData['detector_confidence'])) {
            $score += $anomalyData['detector_confidence'] * 0.3;
        }

        // Factor 3: Historical pattern match
        if (!empty($context['historical_similar'])) {
            $score += min(20, count($context['historical_similar']) * 5);
        }

        return min(100, max(0, (int) round($score)));
    }

    /**
     * Calculate composite risk score (0-100).
     */
    protected function calculateRiskScore(int $severity, int $confidence, array $anomalyData, array $context): int
    {
        // Apply configured weights
        $weights = $this->defaultWeights;

        $baseRisk = (
            ($severity * $weights['severity']) +
            ($confidence * $weights['confidence'])
        );

        // Add business impact factor
        $businessImpact = $this->calculateBusinessImpact($anomalyData, $context);
        $baseRisk += $businessImpact * $weights['business_impact'];

        // Apply risk multipliers from context
        if (!empty($context['risk_multipliers'])) {
            foreach ($context['risk_multipliers'] as $multiplier) {
                $baseRisk *= $multiplier;
            }
        }

        return min(100, max(0, (int) round($baseRisk)));
    }

    /**
     * Calculate business impact factor (0-100).
     */
    protected function calculateBusinessImpact(array $anomalyData, array $context): int
    {
        $impact = 50; // Neutral

        // Factor: Time sensitivity (e.g., end-of-month, audit period)
        if (!empty($context['is_audit_period'])) {
            $impact += 20;
        }

        // Factor: Entity importance (VIP guest, corporate account)
        if (!empty($context['is_vip_entity'])) {
            $impact += 15;
        }

        // Factor: Regulatory implications
        if (!empty($context['has_regulatory_impact'])) {
            $impact += 15;
        }

        return min(100, $impact);
    }

    /**
     * Get human-readable severity factors for UI/audit.
     */
    protected function getSeverityFactors(array $anomalyData, array $context): array
    {
        $factors = [];

        if (isset($anomalyData['financial_impact'])) {
            $factors[] = "Financial impact: \${$anomalyData['financial_impact']}";
        }

        if (isset($anomalyData['aggregate_type'])) {
            $factors[] = "Entity type: {$anomalyData['aggregate_type']}";
        }

        if (isset($anomalyData['type'])) {
            $factors[] = "Anomaly type: {$anomalyData['type']}";
        }

        return $factors;
    }

    /**
     * Get human-readable confidence factors for UI/audit.
     */
    protected function getConfidenceFactors(array $anomalyData, array $context): array
    {
        $factors = [];

        $requiredFields = ['old_value', 'new_value', 'field', 'timestamp'];
        $presentFields = 0;
        foreach($requiredFields as $f) {
            if (isset($anomalyData[$f])) $presentFields++;
        }
        $factors[] = "Data completeness: {$presentFields}/" . count($requiredFields) . " fields";

        if (isset($anomalyData['detector_confidence'])) {
            $factors[] = "Detector confidence: " . round($anomalyData['detector_confidence'], 1) . "%";
        }

        if (!empty($context['historical_similar'])) {
            $factors[] = "Historical matches: " . count($context['historical_similar']);
        }

        return $factors;
    }
}
