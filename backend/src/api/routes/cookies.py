import json
import tempfile
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import SessionDep
from src.core.crypto import decrypt_cookie, encrypt_cookie
from src.db.models.cookie import Cookie
from src.db.session import get_db

logger = structlog.get_logger("tikdown.routes.cookies")

router = APIRouter(prefix="/api/cookies", tags=["cookies"], dependencies=[SessionDep])


def _detect_format(content: str) -> str | None:
    stripped = content.strip()
    if stripped.startswith("["):
        return "json"
    if stripped.startswith("# Netscape HTTP Cookie File") or stripped.startswith("."):
        return "txt"
    return None


def _validate_txt(content: str) -> bool:
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 7:
            for part in parts:
                if "sessionid" in part:
                    return True
    return False


def _validate_json(content: str) -> bool:
    try:
        data = json.loads(content)
        if not isinstance(data, list):
            return False
        for cookie in data:
            if isinstance(cookie, dict) and cookie.get("name") == "sessionid":
                return True
        return False
    except json.JSONDecodeError:
        return False


def _json_to_netscape(content: str) -> str:
    data = json.loads(content)
    lines = ["# Netscape HTTP Cookie File"]
    for c in data:
        if not isinstance(c, dict):
            continue
        domain = c.get("domain", "")
        flag = "TRUE" if c.get("flag", False) or c.get("hostOnly", False) == False else "FALSE"
        path = c.get("path", "/")
        secure = "TRUE" if c.get("secure", False) else "FALSE"
        exp = str(int(c.get("expirationDate", c.get("expires", 0))))
        name = c.get("name", "")
        value = c.get("value", "")
        lines.append(f"{domain}\t{flag}\t{path}\t{secure}\t{exp}\t{name}\t{value}")
    return "\n".join(lines)


def _get_expires_at(content: str, fmt: str) -> float | None:
    if fmt == "json":
        try:
            data = json.loads(content)
            for c in data:
                if isinstance(c, dict) and c.get("name") == "sessionid":
                    exp = c.get("expirationDate") or c.get("expires")
                    if exp:
                        return float(exp)
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    else:
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 7 and "sessionid" in parts[5]:
                try:
                    return float(parts[4])
                except (ValueError, IndexError):
                    pass
    return None


@router.post("")
async def upload_cookie(
    file: UploadFile = File(...),
    db: Annotated[AsyncSession, Depends(get_db)] = Depends(get_db),
) -> dict:
    raw = await file.read()
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")

    fmt = _detect_format(content)
    if not fmt:
        raise HTTPException(
            status_code=400,
            detail="Unrecognized format. Must be Netscape TXT (starting with '# Netscape') or JSON array",
        )

    if fmt == "txt" and not _validate_txt(content):
        raise HTTPException(status_code=400, detail="TXT cookie file must contain 'sessionid'")
    if fmt == "json" and not _validate_json(content):
        raise HTTPException(status_code=400, detail="JSON cookie file must contain 'sessionid'")

    if fmt == "json":
        content = _json_to_netscape(content)
        fmt = "txt"

    expires_at = _get_expires_at(content, "txt")

    encrypted = encrypt_cookie(content)

    import uuid
    from datetime import datetime, UTC, timezone

    now = datetime.now(UTC)
    cookie = Cookie(
        original_format="txt",
        encrypted_content=encrypted,
        status="unverified",
        expires_at=datetime.fromtimestamp(expires_at, tz=timezone.utc) if expires_at else None,
        last_verified_at=None,
    )
    db.add(cookie)
    await db.commit()
    await db.refresh(cookie)

    logger.info("cookie_uploaded", cookie_id=cookie.id, format=fmt)
    return {
        "id": cookie.id,
        "original_format": cookie.original_format,
        "status": cookie.status,
        "expires_at": cookie.expires_at.isoformat() if cookie.expires_at else None,
        "created_at": cookie.created_at.isoformat() if cookie.created_at else None,
    }


@router.get("")
async def list_cookies(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[dict]:
    result = await db.execute(select(Cookie).order_by(Cookie.created_at.desc()))
    cookies = result.scalars().all()
    return [
        {
            "id": c.id,
            "original_format": c.original_format,
            "status": c.status,
            "expires_at": c.expires_at.isoformat() if c.expires_at else None,
            "last_verified_at": c.last_verified_at.isoformat() if c.last_verified_at else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in cookies
    ]


@router.post("/{cookie_id}/test")
async def test_cookie(
    cookie_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    cookie = await db.get(Cookie, cookie_id)
    if not cookie:
        raise HTTPException(status_code=404, detail="Cookie not found")

    plaintext = decrypt_cookie(cookie.encrypted_content)

    from src.core.download_engine import DownloadEngine

    engine = DownloadEngine()
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(plaintext)
        tmp_path = tmp.name

    import os

    try:
        is_valid = await engine.test_cookie(tmp_path)
        from datetime import datetime, UTC, timezone
        cookie.last_verified_at = datetime.now(UTC)
        cookie.status = "valid" if is_valid else "invalid"
        await db.commit()
        logger.info("cookie_tested", cookie_id=cookie_id, valid=is_valid)
        return {"id": cookie.id, "status": cookie.status, "valid": is_valid}
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


@router.delete("/{cookie_id}", status_code=204)
async def delete_cookie(
    cookie_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    cookie = await db.get(Cookie, cookie_id)
    if not cookie:
        raise HTTPException(status_code=404, detail="Cookie not found")
    await db.delete(cookie)
    await db.commit()
    logger.info("cookie_deleted", cookie_id=cookie_id)
