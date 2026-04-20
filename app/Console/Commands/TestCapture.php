<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use App\Models\ShadowEntry;
use Illuminate\Support\Str;

class TestCapture extends Command
{
    protected $signature = 'fce:test-capture
                            {--source-system= : Source system name}
                            {--event-type= : Event type}
                            {--aggregate-id= : Aggregate ID}
                            {--payload= : JSON payload}';

    protected $description = 'Run silent capture test (no UI, no alerts)';

    public function handle()
    {
        $sourceSystem = $this->option('source-system') ?: 'TEST_PMS';
        $eventType = $this->option('event-type') ?: 'booking.created';
        $aggregateId = $this->option('aggregate-id') ?: 'TEST-FOLIO-001';
        $payload = json_decode($this->option('payload') ?: '{"room_rate": 450.00, "previous_rate": 500.00}', true);

        $entry = ShadowEntry::create([
            'id' => (string) Str::uuid(),
            'event_type' => $eventType,
            'aggregate_id' => $aggregateId,
            'aggregate_type' => 'Folio',
            'payload' => $payload,
            'occurred_at' => now(),
            'idempotency_key' => 'test_' . Str::random(10),
            'source_system' => $sourceSystem,
            'device_id' => 'CONSOLE_TEST',
            'signature' => 'test_sig',
            'version' => 1,
        ]);

        $this->info("Event captured: {$entry->id}");
    }
}
