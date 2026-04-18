<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use App\Models\ShadowEntry;

class PreventReplayAttack
{
    public function handle(Request $request, Closure $next)
    {
        $idempotencyKey = $request->header('X-Idempotency-Key') ?: $request->input('idempotency_key');

        if ($idempotencyKey && ShadowEntry::where('idempotency_key', $idempotencyKey)->exists()) {
            return response()->json(['error' => 'Duplicate event'], 409);
        }

        return $next($request);
    }
}
