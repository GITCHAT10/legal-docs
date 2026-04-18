<?php

namespace App\Modules\Eleone\Listeners;

use App\Core\Events\DemandCreated;
use App\Core\Engines\EleoneDecisionEngine;

class ProcessDemand
{
    public function __construct(protected EleoneDecisionEngine $engine) {}

    public function handle(DemandCreated $event)
    {
        $this->engine->process($event->payload);
    }
}
