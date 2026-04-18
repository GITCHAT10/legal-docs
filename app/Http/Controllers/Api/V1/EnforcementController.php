<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Models\RevenueAnomaly;
use App\Models\EnforcementAction;
use Illuminate\Http\Request;
use Illuminate\Support\Str;

class EnforcementController extends Controller
{
    public function takeAction(Request $request, $id)
    {
        $anomaly = RevenueAnomaly::findOrFail($id);

        $validated = $request->validate([
            'action' => 'required|in:approve,flag,block,freeze',
            'notes' => 'nullable|string',
        ]);

        $action = EnforcementAction::create([
            'id' => (string) Str::uuid(),
            'type' => $validated['action'],
            'payload' => [
                'anomaly_id' => $id,
                'notes' => $validated['notes'],
                'user_id' => 'system_operator', // Placeholder
            ],
        ]);

        $anomaly->status = match($validated['action']) {
            'approve' => 'resolved',
            'flag' => 'reviewing',
            'block', 'freeze' => 'enforced',
        };
        $anomaly->enforcement_triggered = true;
        $anomaly->enforcement_action_id = $action->id;
        $anomaly->save();

        return response()->json([
            'status' => 'success',
            'action_id' => $action->id,
            'new_status' => $anomaly->status,
        ]);
    }
}
