import time

import pytest

from src.core.circuit_breaker import CircuitBreaker
from src.core.circuit_breaker import CircuitState


class TestCircuitBreaker:
    def test_closed_by_default(self):
        cb = CircuitBreaker(max_fails=5)
        assert cb.state == CircuitState.CLOSED
        assert not cb.is_open()

    def test_opens_after_max_fails(self):
        cb = CircuitBreaker(max_fails=3)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.is_open()

    def test_success_resets_counter(self):
        cb = CircuitBreaker(max_fails=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.state == CircuitState.CLOSED
        assert cb._fail_count == 0

    def test_success_before_max_keeps_closed(self):
        cb = CircuitBreaker(max_fails=5)
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.state == CircuitState.CLOSED
        cb.record_failure()
        cb.record_failure()
        assert not cb.is_open()
        assert cb._fail_count == 2

    def test_network_errors_do_not_count(self):
        cb = CircuitBreaker(max_fails=5)
        net_error = ConnectionError("connection refused")
        assert cb.is_network_error(net_error) is True
        cb.record_failure()
        assert cb._fail_count == 1

    def test_non_network_errors_identified(self):
        cb = CircuitBreaker(max_fails=5)
        auth_error = PermissionError("403 Forbidden")
        assert cb.is_network_error(auth_error) is False
        http_error = RuntimeError("429 Too Many Requests")
        assert cb.is_network_error(http_error) is False

    def test_half_open_after_timeout(self):
        cb = CircuitBreaker(max_fails=2, reset_timeout=0.05)
        cb.record_failure()
        cb.record_failure()
        assert cb.is_open()
        time.sleep(0.06)
        assert not cb.is_open()
        assert cb.state == CircuitState.HALF_OPEN

    def test_half_open_success_closes(self):
        cb = CircuitBreaker(max_fails=2, reset_timeout=0.05)
        cb.record_failure()
        cb.record_failure()
        time.sleep(0.06)
        cb.record_success()
        assert cb.state == CircuitState.CLOSED
