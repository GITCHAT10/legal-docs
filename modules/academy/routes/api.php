<?php

use Illuminate\Support\Facades\Route;
use Illuminate\Support\Str;
use Modules\Academy\App\Http\Middleware\AttachMNOSHeaders;
use Modules\Academy\App\Http\Middleware\ValidateMNOSSig;
use Modules\Academy\App\Http\Middleware\CheckPolicyGate;
use Modules\Academy\App\Http\Middleware\FceInterceptor;
use Modules\Academy\App\Http\Middleware\ShadowAutoCommit;

$domains = [
    'institutions', 'campuses', 'programs', 'courses', 'cohorts',
    'instructors', 'learners', 'enrollments', 'attendance', 'assessments',
    'submissions', 'grades', 'transcripts', 'certificates', 'learner-skills',
    'wallet-accounts', 'wallet-transactions', 'fee-plans', 'invoices', 'payments',
    'scholarships', 'refunds', 'audit-logs', 'event-outbox', 'shadow-sync-queue'
];

Route::prefix('v1/modules/academy')
    ->middleware([
        AttachMNOSHeaders::class,
        ValidateMNOSSig::class,
        CheckPolicyGate::class,
        ShadowAutoCommit::class
    ])
    ->group(function () use ($domains) {

    foreach ($domains as $domain) {
        $className = Str::studly(Str::singular($domain));
        $controller = "Modules\\Academy\\App\\Http\\Controllers\\Api\\V1\\{$className}Controller";
        Route::apiResource($domain, $controller);
    }

    Route::prefix('intelligence')->group(function () {
        Route::get('learner-risk/{id}', [\Modules\Academy\App\Http\Controllers\Api\V1\LearnerController::class, 'riskScore']);
        Route::get('skill-gaps/{id}', [\Modules\Academy\App\Http\Controllers\Api\V1\LearnerController::class, 'skillGaps']);
        Route::post('skills/unlock', [\Modules\Academy\App\Http\Controllers\Api\V1\LearnerController::class, 'unlockSkill']);
    });

    Route::post('institutions/{id}/issue-certificate', [\Modules\Academy\App\Http\Controllers\Api\V1\InstitutionController::class, 'issueCertificate']);
});
