<?php
require 'vendor/autoload.php';
$app = require_once 'bootstrap/app.php';
$app->make('Illuminate\Contracts\Console\Kernel')->bootstrap();

use App\Models\ShadowEntry;
use Illuminate\Support\Str;

echo "--- STARTING ECOSYSTEM SIMULATION ---\n";

// 1. BUBBLE Demand
echo "[1/4] BUBBLE capturing demand...\n";
$demandId = (string) Str::uuid();
ShadowEntry::create([
    'id' => $demandId,
    'event_type' => 'DEMAND_CREATED',
    'aggregate_id' => 'DEMAND-101',
    'aggregate_type' => 'Demand',
    'payload' => ['item' => 'Kitchen Supplies', 'amount' => 5000, 'priority' => 'URGENT'],
    'occurred_at' => now(),
    'idempotency_key' => 'sim_' . Str::random(10),
    'signature' => 'sim_sig',
    'source_system' => 'BUBBLE',
    'version' => 1
]);

// 2. ELEONE Decision (Implicit via scanner for this demo)
echo "[2/4] ELEONE processing decisions...\n";

// 3. ELEONE INN Hospitality Billing
echo "[3/4] ELEONE INN posting folio with MIRA tax logic...\n";
$folioId = (string) Str::uuid();
$base = 5000;
$serviceCharge = $base * 0.10;
$subtotal = $base + $serviceCharge;
$tgst = $subtotal * 0.17;

// Simulation of a TAX MISMATCH anomaly (intentional error in actual tgst)
ShadowEntry::create([
    'id' => $folioId,
    'event_type' => 'FOLIO_POSTED',
    'aggregate_id' => 'FOLIO-202',
    'aggregate_type' => 'Folio',
    'payload' => [
        'base_amount' => $base,
        'service_charge' => $serviceCharge,
        'tgst' => $tgst - 50, // INTENTIONAL MISMATCH
        'total' => $subtotal + $tgst - 50
    ],
    'occurred_at' => now(),
    'idempotency_key' => 'sim_' . Str::random(10),
    'signature' => 'sim_sig',
    'source_system' => 'ELEONE_INN',
    'version' => 1
]);

echo "[4/4] AEGIS running anomaly detection...\n";
