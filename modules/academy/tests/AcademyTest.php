<?php

namespace Modules\Academy\Tests;

use PHPUnit\Framework\TestCase;

class AcademyTest extends TestCase
{
    public function test_structure_exists()
    {
        $this->assertTrue(directory_exists('modules/academy/app'));
    }
}

function directory_exists($path)
{
    return is_dir($path);
}
