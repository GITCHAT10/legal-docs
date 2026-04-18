<?php

namespace Tests\Feature;

use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;
use App\Models\ShadowEntry;
use App\Models\RevenueAnomaly;
use Illuminate\Support\Str;

class AnomalyDetectionTest extends TestCase
{
    use RefreshDatabase;

    public function test_detects_value_shave()
    {
        $entry = ShadowEntry::create([
            'id' => (string) Str::uuid(),
            'event_type' => 'booking.created',
            'aggregate_id' => 'FOLIO-1',
            'aggregate_type' => 'Folio',
            'payload' => ['room_rate' => 450, 'previous_rate' => 500],
            'occurred_at' => now(),
            'idempotency_key' => 'key1',
            'signature' => 'sig',
            'version' => 1
        ]);

        $this->artisan('fce:scan-anomalies --since="1 hour ago"')
             ->assertExitCode(0);

        $this->assertDatabaseHas('revenue_anomalies', [
            'type' => 'VALUE_SHAVE',
            'aggregate_id' => 'FOLIO-1'
        ]);

        $anomaly = RevenueAnomaly::first();
        $this->assertGreaterThan(0, $anomaly->risk_score);
    }
}
