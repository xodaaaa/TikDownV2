from __future__ import annotations

import time
from enum import Enum

from src.config import settings


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(self, max_fails: int = 5, reset_timeout: float = 300.0):
        self._max_fails = max_fails
        self._reset_timeout = reset_timeout
        self._state = CircuitState.CLOSED
        self._fail_count = 0
        self._last_fail_time = 0.0

    @property
    def state(self) -> CircuitState:
        return self._state

    def record_failure(self) -> None:
        self._fail_count += 1
        self._last_fail_time = time.monotonic()
        if self._fail_count >= self._max_fails:
            self._state = CircuitState.OPEN

    def record_success(self) -> None:
        self._fail_count = 0
        self._state = CircuitState.CLOSED

    def is_open(self) -> bool:
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._last_fail_time >= self._reset_timeout:
                self._state = CircuitState.HALF_OPEN
                return False
            return True
        return False

    def is_network_error(self, error: Exception) -> bool:
        msg = str(error).lower()
        keywords = ["connection", "timeout", "reset", "refused", "dns", "network"]
        return any(k in msg for k in keywords)
