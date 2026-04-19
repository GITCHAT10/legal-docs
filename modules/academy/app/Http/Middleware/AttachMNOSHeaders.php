<?php

namespace Modules\Academy\App\Http\Middleware;

use Closure;

class AttachMNOSHeaders
{
    public function handle($request, Closure $next)
    {
        $response = $next($request);
        $response->headers->set('X-MNOS-Module', 'ACADEMY');
        return $response;
    }
}
