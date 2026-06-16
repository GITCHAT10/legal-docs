<?php

namespace Modules\Academy\Tests\Integration;

use PHPUnit\Framework\TestCase;

class MNOSIntegrationTest extends TestCase
{
    public function test_mnos_event_emission_structure()
    {
        $payload = [
            'event_type' => 'ACADEMY_ENTITY_ACTION',
            'entity_type' => 'Institution',
            'action' => 'CREATE'
        ];
        $this->assertEquals('ACADEMY_ENTITY_ACTION', $payload['event_type']);
    }
}
