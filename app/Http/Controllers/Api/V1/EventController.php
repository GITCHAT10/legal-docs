<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use App\Models\ShadowEntry;
use Illuminate\Support\Str;

class EventController extends Controller
{
    public function store(Request $request)
    {
        $validated = $request->validate([
            'event_type' => 'required|string',
            'aggregate_id' => 'required|string',
            'aggregate_type' => 'required|string',
            'payload' => 'required|array',
            'occurred_at' => 'required|date',
            'idempotency_key' => 'required|string|unique:shadow_entries,idempotency_key',
            'source_system' => 'nullable|string',
            'device_id' => 'nullable|string',
            'signature' => 'required|string',
        ]);

        $entry = ShadowEntry::create([
            'id' => (string) Str::uuid(),
            'event_type' => $validated['event_type'],
            'aggregate_id' => $validated['aggregate_id'],
            'aggregate_type' => $validated['aggregate_type'],
            'payload' => $validated['payload'],
            'occurred_at' => $validated['occurred_at'],
            'idempotency_key' => $validated['idempotency_key'],
            'source_system' => $validated['source_system'] ?? 'unknown',
            'device_id' => $validated['device_id'] ?? 'unknown',
            'signature' => $validated['signature'],
            'user_agent' => $request->userAgent(),
            'ip_address' => $request->ip(),
            'version' => $validated['payload']['version'] ?? 1,
            'metadata' => $request->input('metadata', []),
        ]);

        return response()->json([
            'status' => 'success',
            'event_id' => $entry->id,
        ], 201);
    }
}
