<?php

namespace Modules\Academy\App\Services\MNOS;

use Illuminate\Support\Facades\DB;
use Exception;

class MnosTransaction
{
    /**
     * Executes a callback within a DB transaction and ensures all MNOS protocols are met.
     * Throws exception on any failure to ensure full rollback.
     */
    public static function execute(callable $callback)
    {
        return DB::transaction(function () use ($callback) {
            $result = $callback();

            if ($result === false) {
                throw new Exception("MNOS Transaction Failure: Callback returned false");
            }

            return $result;
        });
    }
}
