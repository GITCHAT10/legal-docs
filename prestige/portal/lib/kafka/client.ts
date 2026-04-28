# lib/kafka/client.ts
import { Kafka, Producer, logLevel } from 'kafkajs';

export const kafka = new Kafka({
  clientId: 'prestige-concierge-portal',
  brokers: [
    'kafka-broker-1.prestige.mv:9094',
    'kafka-broker-2.prestige.mv:9094',
    'kafka-broker-3.prestige.mv:9094',
  ],
  ssl: true,
  logLevel: logLevel.INFO,
});

export const bookingProducer = kafka.producer({
  idempotent: true,
});

export const emitBookingCreated = async (bookingData: any) => {
  await bookingProducer.connect();
  const event = {
    booking_id: "BK-" + Math.random().toString(36).substr(2, 9).toUpperCase(),
    agent_id: bookingData.agent_id,
    resort_code: bookingData.resort_code,
    pricing: {
      amount_mvr: bookingData.total_mvr,
      currency: 'MVR',
    },
    timestamp: new Date().toISOString(),
  };

  await bookingProducer.send({
    topic: 'prestige.bookings.v1',
    messages: [{
      key: bookingData.agent_id,
      value: JSON.stringify(event),
    }],
  });

  return event;
};
