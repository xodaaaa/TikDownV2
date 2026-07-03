from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.core.cookies import CookieParser, FormatDetector


NETSCAPE_SAMPLE = """# Netscape HTTP Cookie File
.tiktok.com	TRUE	/	TRUE	1785600000	sessionid	FAKE_TEST_SESSION_ID
.tiktok.com	TRUE	/	TRUE	1785600000	tt_csrf_token	FAKE_TEST_CSRF
"""

JSON_SAMPLE = json.dumps(
    [
        {
            "domain": ".tiktok.com",
            "name": "sessionid",
            "value": "FAKE_TEST_SESSION_ID",
            "path": "/",
            "secure": True,
            "httpOnly": True,
            "expirationDate": 1785600000,
        }
    ]
)

INVALID_SAMPLE = "this is not a cookie file"


class TestCookieParser:
    def test_detect_format_netscape(self):
        result = FormatDetector.detect(NETSCAPE_SAMPLE)
        assert result == "txt"

    def test_detect_format_json(self):
        result = FormatDetector.detect(JSON_SAMPLE)
        assert result == "json"

    def test_detect_format_invalid(self):
        result = FormatDetector.detect(INVALID_SAMPLE)
        assert result == "invalid"

    def test_parse_netscape_txt(self):
        parser = CookieParser()
        cookies = parser.parse_netscape(NETSCAPE_SAMPLE)
        assert len(cookies) == 2
        names = {c["name"] for c in cookies}
        assert "sessionid" in names
        assert "tt_csrf_token" in names

    def test_parse_json(self):
        parser = CookieParser()
        cookies = parser.parse_json(JSON_SAMPLE)
        assert len(cookies) == 1
        assert cookies[0]["name"] == "sessionid"
        assert cookies[0]["value"] == "FAKE_TEST_SESSION_ID"

    def test_parse_auto_netscape(self):
        parser = CookieParser()
        result = parser.parse(NETSCAPE_SAMPLE)
        assert result["format"] == "txt"
        assert len(result["cookies"]) == 2

    def test_parse_auto_json(self):
        parser = CookieParser()
        result = parser.parse(JSON_SAMPLE)
        assert result["format"] == "json"
        assert len(result["cookies"]) == 1

    def test_parse_invalid_raises(self):
        parser = CookieParser()
        with pytest.raises(ValueError, match="Formato de cookies no reconocido"):
            parser.parse(INVALID_SAMPLE)

    def test_json_to_netscape_conversion(self):
        parser = CookieParser()
        cookies = parser.parse_json(JSON_SAMPLE)
        netscape = parser.json_to_netscape(cookies)
        assert "# Netscape HTTP Cookie File" in netscape
        assert "sessionid" in netscape
        assert "FAKE_TEST_SESSION_ID" in netscape

    def test_parse_netscape_file_io(self):
        parser = CookieParser()
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            f.write(NETSCAPE_SAMPLE)
            tmp_path = f.name
        try:
            with open(tmp_path) as f:
                content = f.read()
            result = parser.parse(content)
            assert result["format"] == "txt"
            assert len(result["cookies"]) >= 1
        finally:
            Path(tmp_path).unlink(missing_ok=True)
