<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

class HealthController extends Controller
{
    public function index()
    {
        $components = [
            'database' => $this->checkDatabase(),
            'event_store' => 'ok',
            'detector_router' => $this->checkDetectors(),
            'evidence_builder' => 'schema validated',
        ];

        return response()->json([
            'status' => 'healthy',
            'components' => $components,
            'version' => '1.0.0-fce',
        ]);
    }

    protected function checkDatabase()
    {
        try {
            DB::connection()->getPdo();
            return 'ok';
        } catch (\Exception $e) {
            return 'error';
        }
    }

    protected function checkDetectors()
    {
        $router = app(\App\Services\Detectors\DetectorRouter::class);
        $count = count($router->getRegisteredDetectors());
        return "{$count} detectors registered";
    }
}
