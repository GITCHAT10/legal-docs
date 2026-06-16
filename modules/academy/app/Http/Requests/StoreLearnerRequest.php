<?php

namespace Modules\Academy\App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;

class StoreLearnerRequest extends FormRequest
{
    public function authorize() { return true; }
    public function rules()
    {
        return [
            'academy_institution_id' => 'required|uuid|exists:academy_institutions,id',
            'user_id' => 'required|uuid|unique:academy_learners,user_id',
            'student_id' => 'required|string|unique:academy_learners,student_id',
        ];
    }
}
