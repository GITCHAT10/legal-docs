<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Models\RevenueAnomaly;
use Illuminate\Http\Request;

class AnomalyController extends Controller
{
    public function index(Request $request)
    {
        $query = RevenueAnomaly::query();

        if ($request->has('status')) {
            $query->where('status', $request->status);
        }

        if ($request->has('min_risk')) {
            $query->where('risk_score', '>=', $request->min_risk);
        }

        return $query->orderBy('detected_at', 'desc')->paginate(20);
    }

    public function show($id)
    {
        return RevenueAnomaly::with('evidence')->findOrFail($id);
    }
}
