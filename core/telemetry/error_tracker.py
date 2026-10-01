"""
Error Tracking & Diagnostics Module for Phase 4.
Provides Sentry SDK integration when SENTRY_DSN is configured,
alongside an in-memory audit buffer of recent runtime exceptions for the monitoring dashboard.
"""

import os
import sys
import time
import logging
import traceback
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import deque

logger = logging.getLogger("plpo.error_tracker")

class CapturedError:
    """Represents a recorded exception event."""
    def __init__(self, error_type: str, message: str, tb: str, context: Optional[Dict[str, Any]] = None):
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.error_type = error_type
        self.message = message
        self.traceback = tb
        self.context = context or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "type": self.error_type,
            "message": self.message,
            "traceback": self.traceback,
            "context": self.context
        }

class ErrorTracker:
    """
    Enterprise error tracking service.
    Integrates with Sentry and maintains an internal circular ring-buffer.
    """

    def __init__(self, buffer_size: int = 100):
        self.buffer_size = buffer_size
        self._buffer: deque = deque(maxlen=buffer_size)
        self._lock = threading.RLock()
        self.sentry_enabled = False

        self._init_sentry_if_configured()

    def _init_sentry_if_configured(self) -> None:
        dsn = os.environ.get("SENTRY_DSN", "").strip()
        if dsn:
            try:
                import sentry_sdk
                sentry_sdk.init(
                    dsn=dsn,
                    traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.2")),
                    environment=os.environ.get("APP_ENV", "development")
                )
                self.sentry_enabled = True
                logger.info("Initialized Sentry error tracking integration.")
            except ImportError:
                logger.warning("SENTRY_DSN provided but sentry-sdk package is not installed.")
            except Exception as e:
                logger.error(f"Failed to initialize Sentry: {e}")

    def capture_exception(self, exc: Exception, context: Optional[Dict[str, Any]] = None) -> CapturedError:
        """Record an exception with full traceback and contextual metadata."""
        tb_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        err = CapturedError(
            error_type=type(exc).__name__,
            message=str(exc),
            tb=tb_str,
            context=context
        )

        with self._lock:
            self._buffer.append(err)

        logger.error(f"Captured exception [{err.error_type}]: {err.message}", exc_info=exc)

        # Forward to Sentry if active
        if self.sentry_enabled:
            try:
                import sentry_sdk
                with sentry_sdk.push_scope() as scope:
                    if context:
                        for k, v in context.items():
                            scope.set_extra(k, v)
                    sentry_sdk.capture_exception(exc)
            except Exception as e:
                logger.error(f"Failed to forward exception to Sentry: {e}")

        return err

    def get_recent_errors(self, limit: int = 25) -> List[Dict[str, Any]]:
        """Retrieve recent exception history for diagnostics."""
        with self._lock:
            return [err.to_dict() for err in reversed(list(self._buffer))][:limit]

    def clear(self) -> None:
        with self._lock:
            self._buffer.clear()

ERROR_TRACKER = ErrorTracker(buffer_size=100)
