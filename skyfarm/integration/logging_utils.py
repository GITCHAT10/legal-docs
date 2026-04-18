import logging
import json
from datetime import datetime, timezone

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
        }
        # Add extra fields if they exist
        for key, value in record.__dict__.items():
            if key in ["request_id", "event_id", "correlation_id", "tenant_id"]:
                log_entry[key] = value
        return json.dumps(log_entry)

def setup_json_logging():
    logger = logging.getLogger("skyfarm")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

    return logger

logger = setup_json_logging()
