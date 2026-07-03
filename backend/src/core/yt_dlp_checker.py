from __future__ import annotations

import structlog

logger = structlog.get_logger("tikdown.yt_dlp_checker")


def check_yt_dlp_version(pinned_version: str | None = None) -> bool:
    try:
        import yt_dlp

        installed = yt_dlp.__version__ if hasattr(yt_dlp, "__version__") else "unknown"
        if pinned_version and installed != pinned_version:
            logger.critical(
                "yt-dlp version mismatch",
                installed=installed,
                pinned=pinned_version,
            )
            return False
        logger.info("yt-dlp version check passed", version=installed)
        return True
    except ImportError:
        logger.critical("yt-dlp not installed")
        return False
    except Exception as e:
        logger.critical("yt-dlp check failed", error=str(e))
        return False


async def check_latest_yt_dlp_version() -> dict | None:
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest",
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "latest_version": data.get("tag_name", "").lstrip("v"),
                "url": data.get("html_url", ""),
                "published_at": data.get("published_at", ""),
            }
    except Exception as e:
        logger.warning("failed to check latest yt-dlp version", error=str(e))
        return None
