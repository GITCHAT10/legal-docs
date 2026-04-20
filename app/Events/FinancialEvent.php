<?php

namespace App\Events;

abstract class FinancialEvent
{
    protected string $type;
    protected string $aggregateId;
    protected string $aggregateType;
    protected array $payload;
    protected array $metadata;
    protected $occurredAt;

    public function __construct(string $type, string $aggregateId, string $aggregateType, array $payload, array $metadata = [], $occurredAt = null)
    {
        $this->type = $type;
        $this->aggregateId = $aggregateId;
        $this->aggregateType = $aggregateType;
        $this->payload = $payload;
        $this->metadata = $metadata;
        $this->occurredAt = $occurredAt ?: now();
    }

    public function getType(): string { return $this->type; }
    public function getAggregateId(): string { return $this->aggregateId; }
    public function getAggregateType(): string { return $this->aggregateType; }
    public function getPayload(): array { return $this->payload; }
    public function getMetadata(): array { return $this->metadata; }
    public function getOccurredAt() { return $this->occurredAt; }
}
