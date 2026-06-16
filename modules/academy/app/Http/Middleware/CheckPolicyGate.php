<?php

namespace Modules\Academy\App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Modules\Academy\App\Services\MNOS\MnosClient;

class CheckPolicyGate
{
    public function handle(Request $request, Closure $next)
    {
        $userId = $request->header('X-MNOS-User-ID') ?? 'system';
        $action = $request->route()->getName() ?? $request->path();

        $response = MnosClient::policy($userId, $action);

        if (isset($response['allowed']) && !$response['allowed']) {
            return response()->json([
                'mnos' => true,
                'status' => 'error',
                'message' => 'Policy Gate: Access Denied'
            ], 403);
        }

        return $next($request);
    }
}
