<?php

namespace Modules\Academy\App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;

class StoreInstitutionRequest extends FormRequest
{
    public function authorize() { return true; }
    public function rules()
    {
        return [
            'name' => 'required|string|max:255',
            'slug' => 'required|string|unique:academy_institutions,slug',
        ];
    }
}
