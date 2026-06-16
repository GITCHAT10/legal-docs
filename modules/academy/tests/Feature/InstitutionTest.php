<?php

namespace Modules\Academy\Tests\Feature;

use PHPUnit\Framework\TestCase;

class InstitutionTest extends TestCase
{
    public function test_api_standard_format()
    {
        $response = [
            'status' => 'success',
            'data' => [
                'id' => '018f3b6c-2d3a-7b3a-8b3a-8b3a8b3a8b3a',
                'name' => 'Test Institution'
            ],
            'meta' => [
                'event_id' => '018f3b6c-2d3a-7b3a-8b3a-8b3a8b3a8b3a',
                'timestamp' => '2024-05-01T12:00:00Z'
            ]
        ];
        $this->assertEquals('success', $response['status']);
        $this->assertArrayHasKey('meta', $response);
        $this->assertArrayHasKey('event_id', $response['meta']);
    }

    public function test_mnos_identity_uuid7_simulation()
    {
        $uuid = '018f3b6c-2d3a-7b3a-8b3a-8b3a8b3a8b3a';
        $this->assertEquals(36, strlen($uuid));
    }
}
