"""
Unit Tests for Telemetry, Prometheus Metric Collection, and System Health Diagnostics.
"""

import pytest
from core.telemetry import (
    METRICS,
    PrometheusCollector,
    get_system_health,
    get_logger,
    ERROR_TRACKER
)

def test_prometheus_metrics_recording():
    METRICS.record_assessment("Loops", True, 5)
    METRICS.record_misconception_detected("misc_test_01")
    METRICS.record_path_recalc("diagnostic_submission")
    METRICS.record_adversarial_violation("PROMPT_INJECTION")

    exported = METRICS.export_metrics()
    assert "plpo_assessments_total" in exported
    assert "plpo_misconceptions_detected_total" in exported
    assert "plpo_path_reoptimizations_total" in exported
    assert "plpo_adversarial_violations_total" in exported

def test_system_health_checker():
    health = get_system_health()
    assert health["status"] in ("HEALTHY", "DEGRADED")
    assert "services" in health
    assert "database" in health["services"]
    assert "cache" in health["services"]
    assert "system_resources" in health

def test_error_tracker():
    ERROR_TRACKER.clear()
    try:
        raise ValueError("Simulated diagnostic error for testing")
    except ValueError as e:
        err = ERROR_TRACKER.capture_exception(e, context={"student_id": "TEST-001"})
        assert err.error_type == "ValueError"

    recent = ERROR_TRACKER.get_recent_errors(limit=5)
    assert len(recent) == 1
    assert recent[0]["message"] == "Simulated diagnostic error for testing"
    assert recent[0]["context"]["student_id"] == "TEST-001"
