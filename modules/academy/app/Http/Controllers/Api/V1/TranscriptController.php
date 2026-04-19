<?php

namespace Modules\Academy\App\Http\Controllers\Api\V1;

use Modules\Academy\App\Models\Transcript;
use Modules\Academy\App\Services\MNOS\MnosTransaction;
use Illuminate\Http\Request;


class TranscriptController extends BaseAcademyController
{
    public function index()
    {
        return $this->mnosResponse(Transcript::all());
    }

    public function store(Request $request)
    {
        $entity = MnosTransaction::execute(function() use ($request) {
            $data = method_exists($request, 'validated') ? $request->validated() : $request->all();
            return Transcript::create($data);
        });
        return $this->mnosResponse($entity, 'success', 201);
    }

    public function show($id)
    {
        return $this->mnosResponse(Transcript::findOrFail($id));
    }

    public function update(Request $request, $id)
    {
        $entity = MnosTransaction::execute(function() use ($request, $id) {
            $item = Transcript::findOrFail($id);
            $item->update($request->all());
            return $item;
        });
        return $this->mnosResponse($entity);
    }

    public function destroy($id)
    {
        MnosTransaction::execute(function() use ($id) {
            return Transcript::findOrFail($id)->delete();
        });
        return $this->mnosResponse(null, 'success', 204);
    }
}
