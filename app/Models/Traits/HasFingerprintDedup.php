<?php

namespace App\Models\Traits;

trait HasFingerprintDedup
{
    public static function bootHasFingerprintDedup()
    {
        static::creating(function ($model) {
            if (empty($model->fingerprint)) {
                $model->fingerprint = $model->generateFingerprint();
            }
        });
    }

    abstract public function generateFingerprint(): string;
}
