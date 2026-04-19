<?php

namespace Modules\Academy\App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;

class StoreInvoiceRequest extends FormRequest
{
    public function authorize() { return true; }
    public function rules()
    {
        return [
            'academy_learner_id' => 'required|uuid|exists:academy_learners,id',
            'amount' => 'required|numeric|min:0',
            'status' => 'required|string',
        ];
    }
}
