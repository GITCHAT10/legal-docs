<?php

namespace Modules\Academy\App\Http\Controllers\Api\V1;

use Modules\Academy\App\Models\Learner;
use Modules\Academy\App\Services\MNOS\MnosTransaction;
use Illuminate\Http\Request;
use Modules\Academy\App\Http\Requests\StoreLearnerRequest;

class LearnerController extends BaseAcademyController
{
    public function index()
    {
        return $this->mnosResponse(Learner::all());
    }

    public function store(StoreLearnerRequest $request)
    {
        $entity = MnosTransaction::execute(function() use ($request) {
            $data = method_exists($request, 'validated') ? $request->validated() : $request->all();
            return Learner::create($data);
        });
        return $this->mnosResponse($entity, 'success', 201);
    }

    public function show($id)
    {
        return $this->mnosResponse(Learner::findOrFail($id));
    }

    public function update(Request $request, $id)
    {
        $entity = MnosTransaction::execute(function() use ($request, $id) {
            $item = Learner::findOrFail($id);
            $item->update($request->all());
            return $item;
        });
        return $this->mnosResponse($entity);
    }

    public function destroy($id)
    {
        MnosTransaction::execute(function() use ($id) {
            return Learner::findOrFail($id)->delete();
        });
        return $this->mnosResponse(null, 'success', 204);
    }

    public function riskScore($id, \Modules\Academy\App\Services\MNOS\MnosClient $client)
    {
        return $this->mnosResponse($client::eleone('DROPOUT_RISK', $id));
    }

    public function skillGaps($id, \Modules\Academy\App\Services\MNOS\MnosClient $client)
    {
        return $this->mnosResponse($client::eleone('SKILL_GAP', $id));
    }

    public function unlockSkill(Request $request)
    {
        return $this->mnosResponse(['status' => 'success']);
    }
}
