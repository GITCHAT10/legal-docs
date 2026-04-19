import logging
import json
import uuid

class StructuredLogger:
    def __init__(self, name="mnos"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            self.logger.addHandler(handler)

    def info(self, message, **kwargs):
        log_data = {
            "message": message,
            "trace_id": kwargs.get("trace_id", str(uuid.uuid4())),
            "event_id": kwargs.get("event_id"),
            "decision": kwargs.get("decision"),
            "latency": kwargs.get("latency"),
            "shadow_status": kwargs.get("shadow_status")
        }
        self.logger.info(json.dumps(log_data))

logger = StructuredLogger()
