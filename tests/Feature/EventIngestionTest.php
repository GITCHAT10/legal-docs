<?php

namespace Tests\Feature;

use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;
use App\Models\ShadowEntry;
use Illuminate\Support\Str;

class EventIngestionTest extends TestCase
{
    use RefreshDatabase;

    public function test_can_ingest_event()
    {
        $response = $this->postJson('/api/v1/events', [
            'event_type' => 'booking.created',
            'aggregate_id' => 'BOOKING-123',
            'aggregate_type' => 'Booking',
            'payload' => ['room_rate' => 100],
            'occurred_at' => now()->toIso8601String(),
            'idempotency_key' => 'key123',
            'signature' => 'valid_sig',
            'source_system' => 'TEST',
        ]);

        $response->assertStatus(201);
        $this->assertDatabaseHas('shadow_entries', ['aggregate_id' => 'BOOKING-123']);
    }

    public function test_prevents_replay_attack()
    {
        ShadowEntry::create([
            'id' => (string) Str::uuid(),
            'event_type' => 'test',
            'aggregate_id' => '1',
            'aggregate_type' => 'Test',
            'payload' => [],
            'occurred_at' => now(),
            'idempotency_key' => 'dup_key',
            'signature' => 'sig',
            'version' => 1
        ]);

        $response = $this->postJson('/api/v1/events', [
            'event_type' => 'test',
            'aggregate_id' => '2',
            'aggregate_type' => 'Test',
            'payload' => [],
            'occurred_at' => now()->toIso8601String(),
            'idempotency_key' => 'dup_key',
            'signature' => 'sig',
        ]);

        $response->assertStatus(422); // Validation fails on unique constraint
    }
}
