from __future__ import annotations

import json
import re
from typing import Any


class FormatDetector:
    @staticmethod
    def detect(content: str) -> str:
        stripped = content.strip()
        if stripped.startswith("# Netscape") or stripped.startswith("# "):
            return "txt"
        if stripped.startswith("["):
            return "json"
        return "invalid"


class CookieParser:
    @staticmethod
    def parse_netscape(content: str) -> list[dict[str, Any]]:
        cookies = []
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 7:
                cookies.append(
                    {
                        "domain": parts[0],
                        "include_subdomains": parts[1] == "TRUE",
                        "path": parts[2],
                        "secure": parts[3] == "TRUE",
                        "expiration": parts[4],
                        "name": parts[5],
                        "value": parts[6],
                    }
                )
        return cookies

    @staticmethod
    def parse_json(content: str) -> list[dict[str, Any]]:
        data = json.loads(content)
        if not isinstance(data, list):
            raise ValueError("JSON debe ser una lista de objetos")
        cookies = []
        for item in data:
            if not isinstance(item, dict) or "domain" not in item or "name" not in item:
                continue
            cookies.append(
                {
                    "domain": item.get("domain", ""),
                    "include_subdomains": item.get("includeSubdomains", True),
                    "path": item.get("path", "/"),
                    "secure": item.get("secure", False),
                    "expiration": str(item.get("expirationDate", "0")),
                    "name": item["name"],
                    "value": item.get("value", ""),
                }
            )
        return cookies

    @staticmethod
    def parse(content: str) -> dict[str, Any]:
        fmt = FormatDetector.detect(content)
        if fmt == "txt":
            cookies = CookieParser.parse_netscape(content)
            return {"format": "txt", "cookies": cookies}
        elif fmt == "json":
            cookies = CookieParser.parse_json(content)
            return {"format": "json", "cookies": cookies}
        raise ValueError("Formato de cookies no reconocido")

    @staticmethod
    def json_to_netscape(cookies: list[dict[str, Any]]) -> str:
        lines = ["# Netscape HTTP Cookie File"]
        for c in cookies:
            lines.append(
                "\t".join(
                    [
                        c.get("domain", ""),
                        "TRUE" if c.get("include_subdomains", True) else "FALSE",
                        c.get("path", "/"),
                        "TRUE" if c.get("secure", False) else "FALSE",
                        str(c.get("expiration", "0")),
                        c.get("name", ""),
                        c.get("value", ""),
                    ]
                )
            )
        return "\n".join(lines) + "\n"
