from __future__ import annotations

import os
import tempfile
from enum import Enum
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger("tikdown.download_engine")


class ErrorKind(str, Enum):
    AUTH = "auth"
    RATE_LIMIT = "rate_limit"
    IP_BLOCK = "ip_block"
    NETWORK = "network"
    NOT_FOUND = "not_found"
    UNKNOWN = "unknown"


class DownloadEngine:
    def __init__(self):
        self._cookies_temp_dir: str | None = None

    async def _classify_error(self, error: Exception) -> tuple[ErrorKind, str]:
        msg = str(error).lower()
        if "403" in msg:
            return ErrorKind.AUTH, str(error)
        if "429" in msg:
            return ErrorKind.RATE_LIMIT, str(error)
        if "404" in msg:
            return ErrorKind.NOT_FOUND, str(error)
        if isinstance(error, (ConnectionError, TimeoutError)):
            return ErrorKind.NETWORK, str(error)
        net_keywords = ["connection", "timeout", "reset", "refused", "dns", "network"]
        if any(k in msg for k in net_keywords):
            return ErrorKind.NETWORK, str(error)
        return ErrorKind.UNKNOWN, str(error)

    def _write_cookies_temp(self, cookies_content: str) -> str:
        if self._cookies_temp_dir is None:
            self._cookies_temp_dir = tempfile.mkdtemp(prefix="tikdown_cookies_")
        fd, path = tempfile.mkstemp(
            dir=self._cookies_temp_dir, suffix=".txt"
        )
        with os.fdopen(fd, "w") as f:
            f.write(cookies_content)
        return path

    def _cleanup_cookies_temp(self, path: str | None = None) -> None:
        if path and Path(path).exists():
            try:
                Path(path).unlink()
            except OSError:
                pass
        if self._cookies_temp_dir and Path(self._cookies_temp_dir).exists():
            try:
                import shutil

                shutil.rmtree(self._cookies_temp_dir, ignore_errors=True)
            except OSError:
                pass
            self._cookies_temp_dir = None
