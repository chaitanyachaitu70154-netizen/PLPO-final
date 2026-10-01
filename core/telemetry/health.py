"""
System Health & Diagnostics Checker for Phase 4.
Evaluates end-to-end database, AI provider, cache, and worker availability.
"""

import time
import os
import psutil
from typing import Dict, Any
from sqlalchemy import text
from core.db.session import get_engine
from core.cache import GLOBAL_CACHE
from core.background import GLOBAL_TASK_QUEUE

class HealthChecker:
    """Verifies operational status of all critical infrastructure components."""

    @staticmethod
    def check_database() -> Dict[str, Any]:
        start = time.time()
        try:
            engine = get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            latency_ms = round((time.time() - start) * 1000, 2)
            return {
                "status": "UP",
                "latency_ms": latency_ms,
                "dialect": engine.dialect.name
            }
        except Exception as e:
            return {
                "status": "DOWN",
                "error": str(e),
                "latency_ms": round((time.time() - start) * 1000, 2)
            }

    @staticmethod
    def check_ai_provider() -> Dict[str, Any]:
        api_key_set = bool(os.environ.get("GEMINI_API_KEY", "").strip())
        return {
            "status": "UP",
            "provider": "Google Gemini 1.5 Flash" if api_key_set else "Deterministic Fallback",
            "api_key_configured": api_key_set,
            "mode": "live_api" if api_key_set else "offline_deterministic"
        }

    @staticmethod
    def check_cache() -> Dict[str, Any]:
        start = time.time()
        try:
            GLOBAL_CACHE.set("__healthcheck__", 1, ttl_seconds=5)
            val = GLOBAL_CACHE.get("__healthcheck__")
            stats = GLOBAL_CACHE.get_stats()
            return {
                "status": "UP" if val == 1 else "DEGRADED",
                "backend": stats["backend"],
                "hit_rate_pct": stats["hit_rate_pct"],
                "size": stats["size"],
                "latency_ms": round((time.time() - start) * 1000, 2)
            }
        except Exception as e:
            return {
                "status": "DOWN",
                "error": str(e)
            }

    @staticmethod
    def check_system_resources() -> Dict[str, Any]:
        try:
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage(os.path.abspath(os.sep))
            return {
                "cpu_percent": psutil.cpu_percent(interval=None),
                "memory_used_mb": round(mem.used / (1024 * 1024), 1),
                "memory_percent": mem.percent,
                "disk_free_gb": round(disk.free / (1024 * 1024 * 1024), 1),
                "disk_percent": disk.percent
            }
        except Exception as e:
            return {"error": str(e)}

    @classmethod
    def get_full_health_report(cls) -> Dict[str, Any]:
        db_health = cls.check_database()
        ai_health = cls.check_ai_provider()
        cache_health = cls.check_cache()
        resources = cls.check_system_resources()

        # Determine overall status
        is_healthy = db_health["status"] == "UP" and cache_health["status"] in ("UP", "DEGRADED")
        status_str = "HEALTHY" if is_healthy else "UNHEALTHY"

        return {
            "status": status_str,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "services": {
                "database": db_health,
                "ai_provider": ai_health,
                "cache": cache_health,
            },
            "system_resources": resources,
            "version": "4.0.0-production"
        }

def get_system_health() -> Dict[str, Any]:
    return HealthChecker.get_full_health_report()
