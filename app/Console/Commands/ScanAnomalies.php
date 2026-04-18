<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use App\Models\ShadowEntry;
use App\Models\RevenueAnomaly;
use App\Services\Detectors\DetectorRouter;
use App\Services\Scoring\AnomalyScorer;
use App\Events\FinancialEvent;
use App\Events\AnomalyDetected;
use Illuminate\Support\Facades\DB;

class ScanAnomalies extends Command
{
    protected $signature = 'fce:scan-anomalies {--since= : Time since last scan} {--log-only : Only log anomalies} {--output= : Output file}';

    protected $description = 'Run anomaly scanner';

    public function handle(DetectorRouter $router, AnomalyScorer $scorer)
    {
        $since = $this->option('since') ? now()->parse($this->option('since')) : now()->subHour();
        $logOnly = $this->option('log-only');
        $output = $this->option('output');

        $this->info("Scanning entries since {$since->toDateTimeString()}...");

        while (true) {
            $entry = DB::transaction(function () use ($since) {
                $item = ShadowEntry::unprocessed()
                    ->where('occurred_at', '>=', $since)
                    ->orderBy('occurred_at', 'asc')
                    ->lockForUpdate()
                    ->first();

                if ($item) {
                    $item->is_processing = true;
                    $item->save();
                }

                return $item;
            });

            if (!$entry) {
                break;
            }

            $this->processEntry($entry, $router, $scorer, $logOnly, $output);
        }

        $this->info("Scan complete.");
    }

    protected function processEntry($entry, $router, $scorer, $logOnly, $output)
    {
        $event = new class($entry->event_type, $entry->aggregate_id, $entry->aggregate_type, $entry->payload, $entry->metadata ?? [], $entry->occurred_at) extends FinancialEvent {};

        $results = $router->detectWithMetadata($event);

        foreach ($results as $resultData) {
            $result = $resultData['result'];
            $detectorClass = $resultData['detector_class'];

            $scores = $scorer->calculateScores([
                'type' => $result->type,
                'aggregate_type' => $entry->aggregate_type,
                'financial_impact' => $result->metadata['financial_impact'] ?? 0,
                'detector_confidence' => $result->confidence,
                'old_value' => $result->diff['old'] ?? null,
                'new_value' => $result->diff['new'] ?? null,
                'field' => $result->metadata['field'] ?? null,
                'timestamp' => $entry->occurred_at,
            ]);

            if ($logOnly) {
                $message = "Anomaly detected: {$result->type} on {$entry->aggregate_type} {$entry->aggregate_id} (Risk: {$scores['risk_score']}) by {$detectorClass}";
                $this->warn($message);
                if ($output) {
                    file_put_contents($output, $message . PHP_EOL, FILE_APPEND);
                }
            } else {
                $anomaly = RevenueAnomaly::create([
                    'type' => $result->type,
                    'detector_class' => $detectorClass,
                    'aggregate_type' => $entry->aggregate_type,
                    'aggregate_id' => $entry->aggregate_id,
                    'severity_score' => $scores['severity_score'],
                    'confidence_score' => $scores['confidence_score'],
                    'risk_score' => $scores['risk_score'],
                    'scoring_breakdown' => $scores['breakdown'],
                    'diff' => $result->diff,
                    'source_event_id' => $entry->id,
                    'detected_at' => now(),
                ]);

                event(new AnomalyDetected($anomaly));
            }
        }

        $entry->markAsProcessed();
    }
}
