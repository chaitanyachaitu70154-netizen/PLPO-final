"""
Background task processing package for Phase 4.
Executes non-blocking background optimizations, batch LLM generation, and telemetry indexing.
"""

from core.background.task_queue import (
    BackgroundTaskManager,
    TaskStatus,
    TaskInfo,
    GLOBAL_TASK_QUEUE
)

__all__ = [
    "BackgroundTaskManager",
    "TaskStatus",
    "TaskInfo",
    "GLOBAL_TASK_QUEUE"
]
