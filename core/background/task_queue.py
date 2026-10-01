"""
Asynchronous Background Task Manager for Phase 4.
Decouples heavy computational workloads (dynamic path optimization across large topic graphs,
batch LLM drill generation, vector indexing) from the user-facing Streamlit render loop.
"""

import time
import uuid
import logging
import threading
from enum import Enum
from typing import Callable, Any, Dict, Optional, List
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field

logger = logging.getLogger("plpo.background")

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class TaskInfo:
    """Metadata and execution state for a background job."""
    task_id: str
    task_name: str
    status: TaskStatus
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Any = None
    error_message: Optional[str] = None
    execution_time_sec: float = 0.0

class BackgroundTaskManager:
    """
    Manages execution of background jobs using a managed thread pool.
    Thread-safe and observable.
    """

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="plpo_worker")
        self._tasks: Dict[str, TaskInfo] = {}
        self._futures: Dict[str, Future] = {}
        self._lock = threading.RLock()

    def submit_task(self, task_name: str, fn: Callable, *args, **kwargs) -> str:
        """
        Submit a callable for asynchronous execution.
        Returns a unique task_id.
        """
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        now = time.time()

        task_info = TaskInfo(
            task_id=task_id,
            task_name=task_name,
            status=TaskStatus.PENDING,
            created_at=now
        )

        with self._lock:
            self._tasks[task_id] = task_info

        def runner():
            with self._lock:
                task_info.status = TaskStatus.RUNNING
                task_info.started_at = time.time()

            try:
                res = fn(*args, **kwargs)
                with self._lock:
                    task_info.status = TaskStatus.COMPLETED
                    task_info.result = res
                    task_info.completed_at = time.time()
                    task_info.execution_time_sec = round(task_info.completed_at - task_info.started_at, 3)
                logger.info(f"Background task '{task_name}' [{task_id}] completed in {task_info.execution_time_sec}s")
                return res
            except Exception as e:
                with self._lock:
                    task_info.status = TaskStatus.FAILED
                    task_info.error_message = str(e)
                    task_info.completed_at = time.time()
                    task_info.execution_time_sec = round(task_info.completed_at - (task_info.started_at or now), 3)
                logger.error(f"Background task '{task_name}' [{task_id}] failed: {e}", exc_info=True)
                raise

        future = self._executor.submit(runner)
        with self._lock:
            self._futures[task_id] = future

        logger.info(f"Submitted background task '{task_name}' with ID [{task_id}]")
        return task_id

    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """Query state of a submitted task."""
        with self._lock:
            return self._tasks.get(task_id)

    def get_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """Wait for task completion and retrieve result."""
        future = None
        with self._lock:
            future = self._futures.get(task_id)
        if not future:
            raise KeyError(f"Task ID [{task_id}] not found.")
        return future.result(timeout=timeout)

    def list_tasks(self, limit: int = 20) -> List[TaskInfo]:
        """List recently submitted tasks."""
        with self._lock:
            sorted_tasks = sorted(self._tasks.values(), key=lambda t: t.created_at, reverse=True)
            return sorted_tasks[:limit]

    def shutdown(self, wait: bool = True) -> None:
        """Gracefully terminate background workers."""
        logger.info("Shutting down background task executor...")
        self._executor.shutdown(wait=wait)

# Singleton task manager
GLOBAL_TASK_QUEUE = BackgroundTaskManager(max_workers=4)
