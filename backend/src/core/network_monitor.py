import asyncio
import random
import time
from datetime import UTC, datetime

import httpx
import structlog

from src.config import settings

logger = structlog.get_logger("tikdown.network_monitor")


class NetworkMonitor:
    def __init__(self) -> None:
        self._running = False
        self._offline = False
        self._consecutive_failures = 0
        self._offline_since: float | None = None
        self._probe_backoff = 30.0
        self._http_client: httpx.AsyncClient | None = None
        self._event_callbacks: list = []
        self._task: asyncio.Task | None = None

    @property
    def is_offline(self) -> bool:
        return self._offline

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def offline_since(self) -> float | None:
        return self._offline_since

    @property
    def consecutive_failures(self) -> int:
        return self._consecutive_failures

    def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=10.0)
        return self._http_client

    async def probe(self) -> bool:
        try:
            client = self._get_client()
            response = await client.head(
                settings.NETWORK_PROBE_URL,
                follow_redirects=True,
                headers={"User-Agent": "TikDown/1.0"},
            )
            return response.is_success or response.status_code < 500
        except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError):
            return False
        except Exception:
            return False

    def on_event(self, callback) -> None:
        self._event_callbacks.append(callback)

    async def _emit_event(self, event_type: str, payload: dict) -> None:
        for cb in self._event_callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(event_type, payload)
                else:
                    cb(event_type, payload)
            except Exception:
                logger.exception("network_monitor_event_callback_failed")

    async def _run_cycle(self) -> None:
        while self._running:
            online = await self.probe()
            if online:
                if self._offline:
                    duration = time.time() - (self._offline_since or time.time())
                    self._offline = False
                    self._consecutive_failures = 0
                    self._probe_backoff = 30.0
                    await self._emit_event(
                        "network.online",
                        {
                            "since": datetime.fromtimestamp(
                                self._offline_since or time.time(), tz=UTC
                            ).isoformat(),
                            "duration_hours": round(duration / 3600, 1),
                            "new_videos_found": 0,
                        },
                    )
                    logger.info("network_online_restored")
                delay = settings.NETWORK_PROBE_INTERVAL
            else:
                self._consecutive_failures += 1
                if not self._offline and self._consecutive_failures >= settings.NETWORK_OFFLINE_THRESHOLD:
                    self._offline = True
                    self._offline_since = time.time()
                    await self._emit_event(
                        "network.offline",
                        {"since": datetime.fromtimestamp(self._offline_since, tz=UTC).isoformat()},
                    )
                    logger.warning("network_offline_declared")
                if self._offline:
                    delay = self._probe_backoff
                    jitter = random.uniform(0, delay * 0.2)
                    self._probe_backoff = min(self._probe_backoff * 2, 600.0)
                    delay = delay + jitter
                else:
                    delay = settings.NETWORK_PROBE_INTERVAL
            await asyncio.sleep(delay)

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_cycle())
        logger.info("network_monitor_started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
        logger.info("network_monitor_stopped")
