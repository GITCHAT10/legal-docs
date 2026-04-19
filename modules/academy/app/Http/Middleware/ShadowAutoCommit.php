<?php

namespace Modules\Academy\App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Modules\Academy\App\Services\MNOS\MnosClient;
use Illuminate\Support\Str;

class ShadowAutoCommit
{
    public function handle(Request $request, Closure $next)
    {
        $response = $next($request);

        // Blocking Gate: Only finalize if SHADOW succeeds for write operations
        if (in_array($request->method(), ['POST', 'PUT', 'PATCH', 'DELETE'])) {
            if ($response->status() >= 200 && $response->status() < 300) {
                MnosClient::shadow(
                    'API_REQUEST',
                    (string) Str::uuid(),
                    $response->getContent(),
                    $request->method()
                );
            }
        }

        return $response;
    }
}
