<?php

namespace Modules\Academy\App\Events;

use Illuminate\Foundation\Events\Dispatchable;
use Illuminate\Queue\SerializesModels;

class AcademyEvent
{
    use Dispatchable, SerializesModels;

    public $type;
    public $payload;

    public function __construct($type, $payload)
    {
        $this->type = $type;
        $this->payload = $payload;
    }
}
