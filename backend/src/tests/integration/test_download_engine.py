from __future__ import annotations

from pathlib import Path

import pytest

from src.core.download_engine import DownloadEngine, ErrorKind


class TestDownloadEngine:
    @pytest.mark.asyncio
    async def test_error_403_classifies_auth(self):
        engine = DownloadEngine()
        error_kind, _ = await engine._classify_error(
            Exception("HTTP Error 403: Forbidden")
        )
        assert error_kind == ErrorKind.AUTH

    @pytest.mark.asyncio
    async def test_error_429_classifies_rate_limit(self):
        engine = DownloadEngine()
        error_kind, _ = await engine._classify_error(
            Exception("HTTP Error 429: Too Many Requests")
        )
        assert error_kind == ErrorKind.RATE_LIMIT

    @pytest.mark.asyncio
    async def test_error_404_classifies_not_found(self):
        engine = DownloadEngine()
        error_kind, _ = await engine._classify_error(
            Exception("HTTP Error 404: Not Found")
        )
        assert error_kind == ErrorKind.NOT_FOUND

    @pytest.mark.asyncio
    async def test_network_error_classifies_network(self):
        engine = DownloadEngine()
        error_kind, _ = await engine._classify_error(
            ConnectionError("Connection refused")
        )
        assert error_kind == ErrorKind.NETWORK

    @pytest.mark.asyncio
    async def test_timeout_classifies_network(self):
        engine = DownloadEngine()
        error_kind, _ = await engine._classify_error(
            TimeoutError("timed out")
        )
        assert error_kind == ErrorKind.NETWORK

    @pytest.mark.asyncio
    async def test_unknown_error_classifies_unknown(self):
        engine = DownloadEngine()
        error_kind, _ = await engine._classify_error(
            RuntimeError("something unexpected")
        )
        assert error_kind == ErrorKind.UNKNOWN

    def test_cookies_temp_file_creation(self):
        engine = DownloadEngine()
        cookies_content = "# Netscape HTTP Cookie File\n.tiktok.com\tTRUE\t/\tTRUE\t0\tsessionid\tFAKE_TEST"
        path = engine._write_cookies_temp(cookies_content)
        try:
            assert Path(path).exists()
            with open(path) as f:
                assert "sessionid" in f.read()
        finally:
            engine._cleanup_cookies_temp(path)

    def test_cookies_temp_file_cleanup(self):
        engine = DownloadEngine()
        path = engine._write_cookies_temp("test")
        assert Path(path).exists()
        engine._cleanup_cookies_temp(path)
        assert not Path(path).exists()

    def test_temporary_file_created_and_cleaned(self):
        engine = DownloadEngine()
        assert engine._cookies_temp_dir is None
        cookies = "# Netscape HTTP Cookie File\n.tiktok.com\tTRUE\t/\tTRUE\t0\tsessionid\tFAKE_TEST"
        path = engine._write_cookies_temp(cookies)
        try:
            assert Path(path).exists()
            assert engine._cookies_temp_dir is not None
            assert Path(engine._cookies_temp_dir).exists()
        finally:
            engine._cleanup_cookies_temp(path)
            assert not Path(path).exists()
