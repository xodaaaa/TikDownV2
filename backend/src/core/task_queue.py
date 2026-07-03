import asyncio
import threading
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable
from typing import Any, Protocol

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

from src.config import settings

logger = structlog.get_logger("tikdown.task_queue")


class TaskQueue(Protocol):
    def enqueue(self, account_id: str, task: Callable[[], Any]) -> None: ...

    def dequeue(self, account_id: str) -> Callable[[], Any] | None: ...

    def pause(self) -> None: ...

    def resume(self) -> None: ...

    def get_status(self) -> dict[str, Any]: ...


class APSchedulerQueue:
    def __init__(
        self,
        scheduler_db_path: str = "",
        max_concurrent: int | None = None,
    ) -> None:
        self._max_concurrent = (
            max_concurrent if max_concurrent is not None else settings.MAX_CONCURRENT_DOWNLOADS
        )
        self._paused = False
        self._lock = threading.Lock()
        self._queues: dict[str, list[Callable[[], Any]]] = defaultdict(list)
        self._running: dict[str, int] = defaultdict(int)
        self._active_count = 0

        jobstore_path = scheduler_db_path or settings.SCHEDULER_DB_PATH
        jobstore = SQLAlchemyJobStore(url=f"sqlite:///{jobstore_path}")

        self.scheduler = AsyncIOScheduler(
            jobstores={"default": jobstore},
            executors={"default": AsyncIOExecutor()},
            job_defaults={
                "coalesce": True,
                "max_instances": 1,
                "misfire_grace_time": 300,
            },
        )

    def enqueue(self, account_id: str, task: Callable[[], Any]) -> None:
        with self._lock:
            self._queues[account_id].append(task)
            logger.debug("task_enqueued", account_id=account_id)

    def dequeue(self, account_id: str) -> Callable[[], Any] | None:
        with self._lock:
            tasks = self._queues.get(account_id)
            if not tasks:
                return None
            return tasks.pop(0)

    def _round_robin_next(self) -> tuple[str, Callable[[], Any]] | None:
        with self._lock:
            if self._paused:
                return None
            if self._active_count >= self._max_concurrent:
                return None
            account_ids = sorted(self._queues.keys())
            for aid in account_ids:
                if self._running.get(aid, 0) > 0:
                    continue
                tasks = self._queues.get(aid)
                if tasks:
                    task = tasks.pop(0)
                    self._running[aid] += 1
                    self._active_count += 1
                    return aid, task
            return None

    async def _execute_next(self) -> None:
        item = self._round_robin_next()
        if item is None:
            return
        account_id, task = item
        try:
            if asyncio.iscoroutinefunction(task):
                await task()
            else:
                result = task()
                if asyncio.iscoroutine(result):
                    await result
        except Exception:
            logger.exception("task_execution_failed", account_id=account_id)
        finally:
            with self._lock:
                self._running[account_id] = max(0, self._running.get(account_id, 0) - 1)
                self._active_count = max(0, self._active_count - 1)

    async def process_queue(self) -> None:
        await self._execute_next()

    def pause(self) -> None:
        with self._lock:
            self._paused = True
            logger.info("task_queue_paused")

    def resume(self) -> None:
        with self._lock:
            self._paused = False
            logger.info("task_queue_resumed")

    def get_status(self) -> dict[str, Any]:
        with self._lock:
            total = sum(len(tasks) for tasks in self._queues.values())
            return {
                "paused": self._paused,
                "active_count": self._active_count,
                "max_concurrent": self._max_concurrent,
                "queued": total,
                "accounts_with_tasks": {
                    aid: len(tasks) for aid, tasks in self._queues.items() if tasks
                },
            }

    def is_running(self) -> bool:
        return self.scheduler.running

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("apscheduler_started")

    async def shutdown(self, wait: bool = True) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=wait)
            logger.info("apscheduler_shutdown")

    def clear_jobs(self) -> None:
        self.scheduler.remove_all_jobs()
        logger.info("apscheduler_jobs_cleared")

    def add_job(self, *args: Any, **kwargs: Any) -> Any:
        return self.scheduler.add_job(*args, **kwargs)
