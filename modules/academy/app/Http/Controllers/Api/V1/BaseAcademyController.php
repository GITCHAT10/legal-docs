<?php

namespace Modules\Academy\App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use Illuminate\Support\Str;

class BaseAcademyController extends Controller
{
    protected function mnosResponse($data, $status = 'success', $code = 200)
    {
        return response()->json([
            'mnos' => true,
            'module' => 'ACADEMY',
            'transaction_id' => (string) Str::uuid7(),
            'shadow_id' => (string) Str::uuid(),
            'event_id' => (string) Str::uuid(),
            'status' => $status,
            'data' => $data
        ], $code);
    }
}
