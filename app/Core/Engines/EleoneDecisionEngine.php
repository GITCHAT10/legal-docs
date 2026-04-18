<?php

namespace App\Core\Engines;

use App\Core\Events\DecisionMade;

class EleoneDecisionEngine
{
    public function process(array $demand)
    {
        // BRAIN LOGIC
        $fulfillment = $this->decideFulfillment($demand);
        $logistics   = $this->decideLogistics($demand);

        event(new DecisionMade([
            'demand_id' => $demand['demand_id'] ?? 'unknown',
            'fulfillment' => $fulfillment,
            'logistics' => $logistics,
            'compliance_status' => 'APPROVED'
        ]));
    }

    protected function decideFulfillment(array $demand)
    {
        return 'SKYGODOWN';
    }

    protected function decideLogistics(array $demand)
    {
        return ($demand['priority'] ?? '') === 'URGENT' ? 'AIR' : 'SEA';
    }
}
