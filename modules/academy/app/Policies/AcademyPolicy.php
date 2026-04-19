<?php

namespace Modules\Academy\App\Policies;

use Illuminate\Auth\Access\HandlesAuthorization;

class AcademyPolicy
{
    use HandlesAuthorization;

    public function createInstitution($user)
    {
        return in_array($user->role, ['dean', 'admin']);
    }

    public function grade($user)
    {
        return in_array($user->role, ['instructor', 'examiner']);
    }
}
