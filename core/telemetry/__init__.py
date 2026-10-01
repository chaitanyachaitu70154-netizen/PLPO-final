"""
Telemetry, Structured Logging, Metrics, and Error Tracking package for Phase 4.
Provides enterprise observability, Prometheus metrics scraping, and health checks.
"""

from core.telemetry.logger import get_logger, StructuredLogger
from core.telemetry.metrics import METRICS, PrometheusCollector
from core.telemetry.error_tracker import ERROR_TRACKER, ErrorTracker
from core.telemetry.health import HealthChecker, get_system_health

__all__ = [
    "get_logger",
    "StructuredLogger",
    "METRICS",
    "PrometheusCollector",
    "ERROR_TRACKER",
    "ErrorTracker",
    "HealthChecker",
    "get_system_health"
]
