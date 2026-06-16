<?php

namespace Modules\Academy\App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use Modules\Academy\App\Http\Requests\StoreInvoiceRequest;
use Modules\Academy\App\Services\FinanceService;
use Illuminate\Http\Request;

class FinanceController extends Controller
{
    protected $financeService;

    public function __construct(FinanceService $financeService)
    {
        $this->financeService = $financeService;
    }

    public function storeInvoice(StoreInvoiceRequest $request)
    {
        return $this->financeService->createInvoice($request->validated());
    }

    public function storePayment(Request $request)
    {
        return $this->financeService->processPayment($request->all());
    }
}
