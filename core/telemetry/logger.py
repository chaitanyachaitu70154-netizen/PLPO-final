"""
Structured JSON Logger for Phase 4.
Produces machine-parseable JSON log records in production (for Datadog, ELK, CloudWatch)
and clean contextual console logs in local development.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

class JSONLogFormatter(logging.Formatter):
    """Formats log records as structured single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
            "process_id": record.process,
            "thread_name": record.threadName
        }

        # Include structured extra attributes if present
        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            log_obj.update(record.extra_fields)

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)

class StructuredLogger:
    """Wrapper that provides context-enriched logging with user_id, trace_id, and event names."""

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def _log(self, level: int, msg: str, event: Optional[str] = None, user_id: Optional[str] = None, **kwargs):
        if not self._logger.isEnabledFor(level):
            return

        extra = kwargs.copy()
        if event:
            extra["event"] = event
        if user_id:
            extra["user_id"] = user_id

        record = self._logger.makeRecord(
            self._logger.name, level, "(unknown)", 0, msg, (), None
        )
        record.extra_fields = extra
        self._logger.handle(record)

    def debug(self, msg: str, **kwargs):
        self._log(logging.DEBUG, msg, **kwargs)

    def info(self, msg: str, **kwargs):
        self._log(logging.INFO, msg, **kwargs)

    def warning(self, msg: str, **kwargs):
        self._log(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs):
        self._log(logging.ERROR, msg, **kwargs)

    def critical(self, msg: str, **kwargs):
        self._log(logging.CRITICAL, msg, **kwargs)

def get_logger(name: str = "plpo") -> StructuredLogger:
    """Retrieve or configure a structured logger instance."""
    base_logger = logging.getLogger(name)

    if not base_logger.handlers:
        base_logger.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())
        handler = logging.StreamHandler(sys.stdout)

        # In production use JSON formatter, otherwise standard clean format
        if os.environ.get("APP_ENV", "").lower() == "production":
            handler.setFormatter(JSONLogFormatter())
        else:
            handler.setFormatter(logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            ))

        base_logger.addHandler(handler)
        base_logger.propagate = False

    return StructuredLogger(base_logger)
