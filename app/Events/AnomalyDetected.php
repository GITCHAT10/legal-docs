<?php

namespace App\Events;

use App\Models\RevenueAnomaly;
use Illuminate\Broadcasting\Channel;
use Illuminate\Broadcasting\InteractsWithSockets;
use Illuminate\Contracts\Broadcasting\ShouldBroadcast;
use Illuminate\Foundation\Events\Dispatchable;
use Illuminate\Queue\SerializesModels;

class AnomalyDetected implements ShouldBroadcast
{
    use Dispatchable, InteractsWithSockets, SerializesModels;

    public function __construct(public RevenueAnomaly $anomaly) {}

    public function broadcastOn(): array
    {
        return [
            new Channel('anomalies'),
        ];
    }

    public function broadcastAs(): string
    {
        return 'anomaly.detected';
    }
}
