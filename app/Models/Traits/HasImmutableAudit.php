<?php

namespace App\Models\Traits;

trait HasImmutableAudit
{
    public static function bootHasImmutableAudit()
    {
        static::updating(function ($model) {
            if (method_exists($model, 'isImmutableField')) {
                // Implementation for granular check if needed
            } else {
                // By default prevent all updates except soft deletes, processing state or specifically allowed fields
                $allowed = ['deleted_at', 'updated_at', 'is_processing', 'processed_at'];

                $dirty = array_keys($model->getDirty());
                $unallowedDirty = array_diff($dirty, $allowed);

                if (!empty($unallowedDirty)) {
                    throw new \Exception("Model " . get_class($model) . " is immutable. Unallowed fields: " . implode(', ', $unallowedDirty));
                }
            }
        });

        static::deleting(function ($model) {
            throw new \Exception("Model " . get_class($model) . " cannot be deleted.");
        });
    }
}
