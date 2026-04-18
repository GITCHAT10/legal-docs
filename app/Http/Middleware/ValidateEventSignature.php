<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;

class ValidateEventSignature
{
    public function handle(Request $request, Closure $next)
    {
        // Placeholder for HMAC signature verification
        if (!$request->has('signature')) {
            return response()->json(['error' => 'Missing signature'], 401);
        }
        return $next($request);
    }
}
