<?php

namespace Modules\Academy\App\Http\Controllers\Api\V1;

use Modules\Academy\App\Models\Institution;
use Modules\Academy\App\Services\MNOS\MnosTransaction;
use Illuminate\Http\Request;
use Modules\Academy\App\Http\Requests\StoreInstitutionRequest;

class InstitutionController extends BaseAcademyController
{
    public function index()
    {
        return $this->mnosResponse(Institution::all());
    }

    public function store(StoreInstitutionRequest $request)
    {
        $entity = MnosTransaction::execute(function() use ($request) {
            $data = method_exists($request, 'validated') ? $request->validated() : $request->all();
            return Institution::create($data);
        });
        return $this->mnosResponse($entity, 'success', 201);
    }

    public function show($id)
    {
        return $this->mnosResponse(Institution::findOrFail($id));
    }

    public function update(Request $request, $id)
    {
        $entity = MnosTransaction::execute(function() use ($request, $id) {
            $item = Institution::findOrFail($id);
            $item->update($request->all());
            return $item;
        });
        return $this->mnosResponse($entity);
    }

    public function destroy($id)
    {
        MnosTransaction::execute(function() use ($id) {
            return Institution::findOrFail($id)->delete();
        });
        return $this->mnosResponse(null, 'success', 204);
    }

    public function issueCertificate(Request $request, \Modules\Academy\App\Actions\IssueCertificate $action)
    {
        $result = MnosTransaction::execute(fn() => $action->execute($request->all()));
        return $this->mnosResponse($result);
    }
}
