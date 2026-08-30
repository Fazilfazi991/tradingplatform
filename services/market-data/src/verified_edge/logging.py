import json
import logging
from typing import Any


def log_event(logger: logging.Logger, event: str, **fields: Any) -> None:
    safe = {
        key: value
        for key, value in fields.items()
        if "token" not in key.lower() and "secret" not in key.lower()
    }
    logger.info(json.dumps({"event": event, **safe}, sort_keys=True, default=str))
