<?php

namespace App\Core\Events;

use Illuminate\Foundation\Events\Dispatchable;

class DemandCreated
{
    use Dispatchable;

    public function __construct(public array $payload) {}
}
