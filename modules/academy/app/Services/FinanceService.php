<?php

namespace Modules\Academy\App\Services;

use Modules\Academy\App\Models\Invoice;
use Modules\Academy\App\Models\Payment;

class FinanceService
{
    public function createInvoice(array $data)
    {
        // 1. Validate against FCE core logic (simulated)
        // 2. Persist locally
        return Invoice::create($data);
    }

    public function processPayment(array $data)
    {
        // 1. Capture via FCE core logic (simulated)
        // 2. Update local state
        return Payment::create($data);
    }
}
