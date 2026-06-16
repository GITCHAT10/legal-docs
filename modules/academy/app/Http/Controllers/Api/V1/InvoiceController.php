<?php

namespace Modules\Academy\App\Http\Controllers\Api\V1;

use Modules\Academy\App\Models\Invoice;
use Modules\Academy\App\Services\MNOS\MnosTransaction;
use Illuminate\Http\Request;
use Modules\Academy\App\Http\Requests\StoreInvoiceRequest;

class InvoiceController extends BaseAcademyController
{
    public function index()
    {
        return $this->mnosResponse(Invoice::all());
    }

    public function store(StoreInvoiceRequest $request)
    {
        $entity = MnosTransaction::execute(function() use ($request) {
            $data = method_exists($request, 'validated') ? $request->validated() : $request->all();
            return Invoice::create($data);
        });
        return $this->mnosResponse($entity, 'success', 201);
    }

    public function show($id)
    {
        return $this->mnosResponse(Invoice::findOrFail($id));
    }

    public function update(Request $request, $id)
    {
        $entity = MnosTransaction::execute(function() use ($request, $id) {
            $item = Invoice::findOrFail($id);
            $item->update($request->all());
            return $item;
        });
        return $this->mnosResponse($entity);
    }

    public function destroy($id)
    {
        MnosTransaction::execute(function() use ($id) {
            return Invoice::findOrFail($id)->delete();
        });
        return $this->mnosResponse(null, 'success', 204);
    }
}
