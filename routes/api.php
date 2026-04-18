<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\Api\V1\EventController;
use App\Http\Controllers\Api\V1\HealthController;
use App\Http\Controllers\Api\V1\DashboardController;
use App\Http\Controllers\Api\V1\AnomalyController;
use App\Http\Controllers\Api\V1\EnforcementController;

Route::prefix('v1')->group(function () {
    Route::post('/events', [EventController::class, 'store']);
    Route::get('/health', [HealthController::class, 'index']);

    Route::get('/dashboard/stats', [DashboardController::class, 'stats']);

    Route::get('/anomalies', [AnomalyController::class, 'index']);
    Route::get('/anomalies/{id}', [AnomalyController::class, 'show']);

    Route::post('/anomalies/{id}/action', [EnforcementController::class, 'takeAction']);
});
