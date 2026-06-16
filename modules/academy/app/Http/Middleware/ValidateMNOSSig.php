<?php

namespace Modules\Academy\App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;

class ValidateMNOSSig
{
    public function handle(Request $request, Closure $next)
    {
        $signature = $request->header('X-MNOS-Signature');
        $timestamp = $request->header('X-Timestamp');

        if (!$signature || !$timestamp) {
            return response()->json([
                'status' => 'error',
                'message' => 'Missing Security Headers'
            ], 401);
        }

        // Production-grade signature verification logic
        $secret = config('academy.mnos_secret');
        $canonicalString = $request->method() . "\n" . $request->path() . "\n" . $timestamp;
        $expectedSignature = hash_hmac('sha256', $canonicalString, $secret);

        if (!hash_equals($expectedSignature, $signature)) {
            return response()->json([
                'status' => 'error',
                'message' => 'Invalid MNOS Signature'
            ], 403);
        }

        return $next($request);
    }
}
