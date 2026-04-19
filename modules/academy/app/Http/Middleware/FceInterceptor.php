<?php

namespace Modules\Academy\App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Modules\Academy\App\Services\MNOS\MnosClient;

class FceInterceptor
{
    public function handle(Request $request, Closure $next)
    {
        $financialRoutes = ['invoices', 'payments', 'transactions'];

        $isFinancial = collect($financialRoutes)->contains(function ($route) use ($request) {
            return str_contains($request->path(), $route);
        });

        if ($isFinancial && in_array($request->method(), ['POST', 'PUT', 'PATCH'])) {
             // Block if FCE call fails (Fail-closed)
             MnosClient::finance([
                 'payload' => $request->all(),
                 'method' => $request->method(),
                 'path' => $request->path(),
                 'timestamp' => now()->toIso8601String()
             ]);
        }

        return $next($request);
    }
}
