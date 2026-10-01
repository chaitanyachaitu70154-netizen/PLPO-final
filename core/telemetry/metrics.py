"""
Prometheus Metrics Instrumentation for Phase 4.
Collects system-level, algorithmic, and security telemetry for Prometheus/Grafana dashboards.
"""

import time
from typing import Dict, Any, Optional
from prometheus_client import (
    Counter, Histogram, Gauge, generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST
)

# Dedicated registry for PLPO metrics
REGISTRY = CollectorRegistry(auto_describe=True)

# 1. Adaptive Learning Loop Counters
ASSESSMENTS_TOTAL = Counter(
    "plpo_assessments_total",
    "Total diagnostic and practice assessment attempts processed",
    ["topic", "is_correct", "confidence_bucket"],
    registry=REGISTRY
)

PATH_REOPTIMIZATIONS_TOTAL = Counter(
    "plpo_path_reoptimizations_total",
    "Total dynamic learning path recalculations triggered",
    ["trigger"],
    registry=REGISTRY
)

MISCONCEPTIONS_DETECTED_TOTAL = Counter(
    "plpo_misconceptions_detected_total",
    "Total cognitive misconceptions identified from assessment distractors",
    ["misconception_id"],
    registry=REGISTRY
)

MISCONCEPTIONS_REMEDIATED_TOTAL = Counter(
    "plpo_misconceptions_remediated_total",
    "Total misconceptions successfully remediated through follow-up assessment",
    ["misconception_id"],
    registry=REGISTRY
)

# 2. AI Tutor & Adversarial Resilience Metrics
AI_REQUESTS_TOTAL = Counter(
    "plpo_ai_requests_total",
    "Total server-side AI requests made",
    ["provider", "call_type", "status"],
    registry=REGISTRY
)

ADVERSARIAL_VIOLATIONS_TOTAL = Counter(
    "plpo_adversarial_violations_total",
    "Total blocked malicious prompt injections or invalid parameters",
    ["violation_type"],
    registry=REGISTRY
)

# 3. Latency Histograms
PATH_OPTIMIZATION_SECONDS = Histogram(
    "plpo_path_optimization_duration_seconds",
    "Time taken to recalculate dynamic learning path through prerequisite DAG",
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=REGISTRY
)

AI_RESPONSE_SECONDS = Histogram(
    "plpo_ai_response_duration_seconds",
    "Time taken to generate server-side AI responses",
    ["call_type"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0],
    registry=REGISTRY
)

DB_QUERY_SECONDS = Histogram(
    "plpo_db_query_duration_seconds",
    "Database execution duration",
    ["operation"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25],
    registry=REGISTRY
)

# 4. State Gauges
ACTIVE_SESSIONS_GAUGE = Gauge(
    "plpo_active_sessions",
    "Current active user sessions",
    registry=REGISTRY
)

SYSTEM_MASTERY_AVERAGE = Gauge(
    "plpo_system_mastery_average_pct",
    "Average student mastery across all active topics",
    registry=REGISTRY
)

class PrometheusCollector:
    """Helper facade for application code to emit metrics cleanly."""

    @staticmethod
    def record_assessment(topic: str, is_correct: bool, confidence: int):
        bucket = "high" if confidence >= 4 else "medium" if confidence == 3 else "low"
        ASSESSMENTS_TOTAL.labels(
            topic=topic,
            is_correct=str(is_correct).lower(),
            confidence_bucket=bucket
        ).inc()

    @staticmethod
    def record_path_recalc(trigger: str = "reassessment"):
        PATH_REOPTIMIZATIONS_TOTAL.labels(trigger=trigger).inc()

    @staticmethod
    def record_misconception_detected(misc_id: str):
        MISCONCEPTIONS_DETECTED_TOTAL.labels(misconception_id=misc_id).inc()

    @staticmethod
    def record_misconception_remediated(misc_id: str):
        MISCONCEPTIONS_REMEDIATED_TOTAL.labels(misconception_id=misc_id).inc()

    @staticmethod
    def record_ai_request(provider: str, call_type: str, status: str = "success"):
        AI_REQUESTS_TOTAL.labels(provider=provider, call_type=call_type, status=status).inc()

    @staticmethod
    def record_adversarial_violation(violation_type: str):
        ADVERSARIAL_VIOLATIONS_TOTAL.labels(violation_type=violation_type).inc()

    @staticmethod
    def export_metrics() -> str:
        """Export metrics formatted for Prometheus scraping."""
        return generate_latest(REGISTRY).decode("utf-8")

METRICS = PrometheusCollector()
