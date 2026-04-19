<?php

namespace Modules\Academy\App\Http\Controllers\Api\V1;

use Modules\Academy\App\Models\Attendance;
use Modules\Academy\App\Services\MNOS\MnosTransaction;
use Illuminate\Http\Request;


class AttendanceController extends BaseAcademyController
{
    public function index()
    {
        return $this->mnosResponse(Attendance::all());
    }

    public function store(Request $request)
    {
        $entity = MnosTransaction::execute(function() use ($request) {
            $data = method_exists($request, 'validated') ? $request->validated() : $request->all();
            return Attendance::create($data);
        });
        return $this->mnosResponse($entity, 'success', 201);
    }

    public function show($id)
    {
        return $this->mnosResponse(Attendance::findOrFail($id));
    }

    public function update(Request $request, $id)
    {
        $entity = MnosTransaction::execute(function() use ($request, $id) {
            $item = Attendance::findOrFail($id);
            $item->update($request->all());
            return $item;
        });
        return $this->mnosResponse($entity);
    }

    public function destroy($id)
    {
        MnosTransaction::execute(function() use ($id) {
            return Attendance::findOrFail($id)->delete();
        });
        return $this->mnosResponse(null, 'success', 204);
    }
}
