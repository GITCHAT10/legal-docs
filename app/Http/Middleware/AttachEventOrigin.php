<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;

class AttachEventOrigin
{
    public function handle(Request $request, Closure $next)
    {
        $request->merge([
            'source_system' => $request->header('X-Source-System') ?: $request->input('source_system', 'unknown'),
            'device_id' => $request->header('X-Device-Id') ?: $request->input('device_id', 'unknown'),
        ]);
        return $next($request);
    }
}
