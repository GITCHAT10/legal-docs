<?php

namespace App\Providers;

use Illuminate\Support\ServiceProvider;
use App\Services\Detectors\DetectorRouter;
use App\Services\Scoring\AnomalyScorer;
use App\Services\Evidence\EvidenceBuilder;

class AppServiceProvider extends ServiceProvider
{
    /**
     * Register any application services.
     */
    public function register(): void
    {
        $this->app->singleton(DetectorRouter::class, function ($app) {
            $router = new DetectorRouter($app);
            $router->registerFromConfig(config('detectors', []));
            return $router;
        });

        $this->app->singleton(AnomalyScorer::class, function ($app) {
            return new AnomalyScorer(config('scoring.weights', []));
        });

        $this->app->singleton(EvidenceBuilder::class, function ($app) {
            return new EvidenceBuilder(config('evidence.schemas.default') ?? []);
        });
    }

    /**
     * Bootstrap any application services.
     */
    public function boot(): void
    {
        //
    }
}
