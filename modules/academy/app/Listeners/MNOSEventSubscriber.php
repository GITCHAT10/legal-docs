<?php

namespace Modules\Academy\App\Listeners;

use Modules\Academy\App\Events\AcademyEvent;

class MNOSEventSubscriber
{
    public function handleAcademyEvent(AcademyEvent $event)
    {
        // Logic to push to event_outbox
    }

    public function subscribe($events)
    {
        $events->listen(
            AcademyEvent::class,
            [MNOSEventSubscriber::class, 'handleAcademyEvent']
        );
    }
}
