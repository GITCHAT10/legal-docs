<?php

namespace Modules\Academy\App\Services\MNOS;

use Illuminate\Support\Facades\Http;
use Exception;

class MnosClient
{
    protected static function coreUrl()
    {
        return config('academy.mnos_core_url', 'http://mnos-core');
    }

    public static function call($method, $endpoint, $payload = [])
    {
        try {
            $timestamp = now()->toIso8601String();
            $secret = config('academy.mnos_secret', 'placeholder');

            // Canonical string for signature: METHOD\nPATH\nTIMESTAMP
            $canonicalString = strtoupper($method) . "\n" . $endpoint . "\n" . $timestamp;
            $signature = hash_hmac('sha256', $canonicalString, $secret);

            $response = Http::withHeaders([
                'X-MNOS-Signature' => $signature,
                'X-Timestamp' => $timestamp,
                'Accept' => 'application/json'
            ])->$method(self::coreUrl() . $endpoint, $payload);

            if ($response->failed()) {
                throw new Exception("MNOS CORE Error: [$endpoint] Status " . $response->status() . " - " . $response->body());
            }

            return $response->json();
        } catch (Exception $e) {
            // Fail-closed principle: Stop execution on any Core failure
            throw new Exception("MNOS CORE Unreachable or Failed: " . $e->getMessage());
        }
    }

    public static function event($type, $payload)
    {
        return self::call('post', '/v1/mnos/events', [
            'event_type' => $type,
            'payload' => $payload,
            'timestamp' => now()->toIso8601String()
        ]);
    }

    public static function shadow($entityType, $entityId, $payload, $action)
    {
        return self::call('post', '/v1/mnos/shadow', [
            'entity_type' => $entityType,
            'entity_id' => $entityId,
            'payload' => $payload,
            'action' => $action
        ]);
    }

    public static function eleone($type, $entityId, $payload = [])
    {
        return self::call('post', '/v1/mnos/eleone/evaluate', [
            'type' => $type,
            'entity_id' => $entityId,
            'payload' => $payload
        ]);
    }

    public static function policy($userId, $action)
    {
        return self::call('post', '/v1/policy/check', [
            'user_id' => $userId,
            'action' => $action
        ]);
    }

    public static function finance($payload)
    {
        return self::call('post', '/v1/mnos/fce/intercept', $payload);
    }
}
