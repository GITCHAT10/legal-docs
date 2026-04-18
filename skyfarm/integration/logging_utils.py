import logging
import json
import os
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
        # Standardized fields for integration observability (Phase 6)
        for key in ["request_id", "event_id", "correlation_id", "tenant_id", "category", "status"]:
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)
            elif isinstance(record.args, dict) and key in record.args:
                log_entry[key] = record.args[key]
            elif hasattr(record, 'extra') and record.extra and key in record.extra:
                 log_entry[key] = record.extra[key]

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
