"""
Service layer package for Phase 4.
Establishes clean, decoupled API boundaries between UI controllers and core engines.
"""

from core.services.adaptive_service import AdaptiveService, AdaptiveLoopResult
from core.services.student_service import StudentService

__all__ = [
    "AdaptiveService",
    "AdaptiveLoopResult",
    "StudentService"
]
