import random
import time

from src.config import settings


class ExponentialBackoff:
    def __init__(
        self,
        min_delay: float | None = None,
        max_delay: float | None = None,
        max_backoff: float | None = None,
    ) -> None:
        self._min_delay = min_delay if min_delay is not None else settings.MIN_DELAY_SECONDS
        self._max_delay = max_delay if max_delay is not None else settings.MAX_DELAY_SECONDS
        self._max_backoff = (
            max_backoff if max_backoff is not None else settings.BACKOFF_MAX_SECONDS
        )
        self._attempt = 0

    def get_delay(self, attempt: int | None = None) -> float:
        if attempt is not None:
            self._attempt = attempt
        self._attempt += 1
        n = self._attempt
        exponential = min(self._max_delay * (2 ** (n - 1)), self._max_backoff)
        jitter = random.uniform(0, exponential * 0.5)
        delay = exponential + jitter
        return max(self._min_delay, min(delay, self._max_backoff))

    def reset(self) -> None:
        self._attempt = 0

    @property
    def attempt(self) -> int:
        return self._attempt
