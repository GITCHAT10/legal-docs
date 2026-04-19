<?php

namespace Modules\Academy\App\Http\Controllers\Api\V1;

use Modules\Academy\App\Models\EventOutbox;
use Modules\Academy\App\Services\MNOS\MnosTransaction;
use Illuminate\Http\Request;


class EventOutboxController extends BaseAcademyController
{
    public function index()
    {
        return $this->mnosResponse(EventOutbox::all());
    }

    public function store(Request $request)
    {
        $entity = MnosTransaction::execute(function() use ($request) {
            $data = method_exists($request, 'validated') ? $request->validated() : $request->all();
            return EventOutbox::create($data);
        });
        return $this->mnosResponse($entity, 'success', 201);
    }

    public function show($id)
    {
        return $this->mnosResponse(EventOutbox::findOrFail($id));
    }

    public function update(Request $request, $id)
    {
        $entity = MnosTransaction::execute(function() use ($request, $id) {
            $item = EventOutbox::findOrFail($id);
            $item->update($request->all());
            return $item;
        });
        return $this->mnosResponse($entity);
    }

    public function destroy($id)
    {
        MnosTransaction::execute(function() use ($id) {
            return EventOutbox::findOrFail($id)->delete();
        });
        return $this->mnosResponse(null, 'success', 204);
    }
}
