<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Models\RevenueAnomaly;
use App\Models\ShadowEntry;
use Illuminate\Http\Request;

class DashboardController extends Controller
{
    public function stats()
    {
        return response()->json([
            'trust_score' => 98.5,
            'total_transactions' => ShadowEntry::count(),
            'flagged_anomalies' => RevenueAnomaly::where('status', 'detected')->count(),
            'resolved_anomalies' => RevenueAnomaly::where('status', 'resolved')->count(),
            'trends' => [
                ['date' => now()->subDays(6)->toDateString(), 'count' => 5],
                ['date' => now()->subDays(5)->toDateString(), 'count' => 8],
                ['date' => now()->subDays(4)->toDateString(), 'count' => 3],
                ['date' => now()->subDays(3)->toDateString(), 'count' => 12],
                ['date' => now()->subDays(2)->toDateString(), 'count' => 7],
                ['date' => now()->subDays(1)->toDateString(), 'count' => 10],
                ['date' => now()->toDateString(), 'count' => 4],
            ],
            'module_risk' => [
                'BUBBLE' => 12,
                'ELEONE' => 5,
                'ELEONE INN' => 22,
                'SKYGODOWN' => 8,
                'ATOLLAIRWAYS' => 3,
            ]
        ]);
    }
}
