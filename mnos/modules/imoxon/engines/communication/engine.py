class CommunicationEngine:
    def __init__(self, shadow, events):
        self.shadow = shadow
        self.events = events

    def send_message(self, sender_id: str, receiver_id: str, content: str, context: str):
        message = {
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "content": content,
            "context": context,
            "timestamp": "now"
        }
        self.shadow.record_action("comm.message_sent", {"from": sender_id, "to": receiver_id, "context": context})
        self.events.trigger("MESSAGE_SENT", message)
        return message
