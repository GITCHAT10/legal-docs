<?php

namespace Modules\Academy\Database\Seeders;

use Illuminate\Database\Seeder;
use Modules\Academy\App\Models\Institution;
use Modules\Academy\App\Models\Program;
use Modules\Academy\App\Models\Course;
use Modules\Academy\App\Models\Cohort;
use Modules\Academy\App\Models\Learner;

class AcademyDemoSeeder extends Seeder
{
    public function run()
    {
        $inst = Institution::create(['name' => 'MNOS Global Academy', 'slug' => 'mga']);
        $prog = Program::create(['academy_institution_id' => $inst->id, 'name' => 'Digital Sovereignity']);
        $course = Course::create(['academy_program_id' => $prog->id, 'name' => 'Module Development', 'code' => 'MOD-101']);
        $cohort = Cohort::create(['academy_course_id' => $course->id, 'name' => 'Spring 2024', 'start_date' => '2024-03-01', 'end_date' => '2024-06-01']);
    }
}
