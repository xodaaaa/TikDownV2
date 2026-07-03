import pytest

from src.core.backoff import ExponentialBackoff


class TestExponentialBackoff:
    def test_delay_increases_with_attempts(self):
        b = ExponentialBackoff(min_delay=1, max_delay=10, max_backoff=1800)
        d1 = b.get_delay(1)
        d2 = b.get_delay(2)
        d3 = b.get_delay(3)
        assert d3 >= d2 >= d1

    def test_jitter_randomness(self):
        b = ExponentialBackoff(min_delay=10, max_delay=10, max_backoff=1800)
        delays = [b.get_delay(1) for _ in range(100)]
        assert all(d >= 10 for d in delays)
        assert len(set(delays)) > 1

    def test_caps_at_max_delay(self):
        b = ExponentialBackoff(min_delay=1, max_delay=10, max_backoff=1800)
        d = b.get_delay(100)
        assert d <= 1800

    def test_max_delay_with_jitter(self):
        b = ExponentialBackoff(min_delay=1, max_delay=10, max_backoff=1800)
        for _ in range(50):
            d = b.get_delay(100)
            assert d >= 1

    @pytest.mark.asyncio
    async def test_wait_respects_delay(self):
        import asyncio
        import time

        b = ExponentialBackoff(min_delay=0.01, max_delay=0.01, max_backoff=1800)
        start = time.monotonic()
        delay = b.get_delay(1)
        await asyncio.sleep(delay)
        elapsed = time.monotonic() - start
        assert elapsed >= 0.008

    def test_get_delay_never_zero(self):
        b = ExponentialBackoff(min_delay=0.5, max_delay=10, max_backoff=1800)
        for attempt in range(1, 10):
            assert b.get_delay(attempt) >= 0.5
