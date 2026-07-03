import hashlib
import hmac
import json
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Annotated

import structlog
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError
from fastapi import Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.crypto import get_secret_key, rotate_secret_key
from src.db.models.admin import Admin
from src.db.session import get_db

logger = structlog.get_logger("tikdown.auth")

_ph = PasswordHasher()

COOKIE_NAME = "tikdown_session"

SALT_LENGTH = 16
SIGNATURE_LENGTH = 64  # SHA-256 hex


class AuthResponse(BaseModel):
    authenticated: bool
    needs_setup: bool


async def check_needs_setup(db: AsyncSession) -> bool:
    result = await db.execute(select(Admin).limit(1))
    return result.scalar_one_or_none() is None


def hash_password(plain: str) -> str:
    return _ph.hash(plain)


def verify_password(plain: str, hash_value: str) -> bool:
    try:
        return _ph.verify(hash_value, plain)
    except (VerifyMismatchError, VerificationError):
        return False


def _make_session_payload(created_at: float | None = None) -> str:
    payload = {"iat": int(created_at or time.time()), "exp": 0}
    return json.dumps(payload, separators=(",", ":"))


def create_session_token(secret_key: str) -> str:
    payload_b64 = _base64url_encode(_make_session_payload().encode())
    sig = hmac.new(
        secret_key.encode(), payload_b64.encode(), hashlib.sha256
    ).hexdigest()
    return f"{payload_b64}.{sig}"


def verify_session_token(token: str, secret_key: str) -> dict | None:
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_b64, sig = parts
        expected_sig = hmac.new(
            secret_key.encode(), payload_b64.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        payload_raw = _base64url_decode(payload_b64)
        payload = json.loads(payload_raw)
        return payload
    except (ValueError, json.JSONDecodeError, Exception):
        return None


def _base64url_encode(data: bytes) -> str:
    return (
        __import__("base64").urlsafe_b64encode(data).rstrip(b"=").decode("ascii")
    )


def _base64url_decode(data: str) -> bytes:
    padded = data + "=" * (4 - len(data) % 4)
    return __import__("base64").urlsafe_b64decode(padded)


async def _get_session_from_request(request: Request) -> str | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[len("Bearer "):]
    return token


async def require_auth(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> bool:
    needs = await check_needs_setup(db)
    if needs:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"needs_setup": True, "authenticated": False},
        )
    token = await _get_session_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    secret_key = get_secret_key()
    payload = verify_session_token(token, secret_key)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )
    return True


async def get_current_user_id(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> str:
    await require_auth(request, db)
    return "admin"


SessionDep = Annotated[bool, Depends(require_auth)]


def set_session_cookie(response: Response, secret_key: str) -> None:
    token = create_session_token(secret_key)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        path="/",
        max_age=None,
    )


def delete_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="lax",
    )


async def handle_force_reset(db: AsyncSession) -> bool:
    if not settings.FORCE_RESET:
        return False
    result = await db.execute(select(Admin).limit(1))
    admin = result.scalar_one_or_none()
    if admin is None:
        logger.info("force_reset_noop_no_admin_exists")
        return False
    await db.delete(admin)
    await db.commit()
    new_secret = rotate_secret_key()
    logger.info("force_reset_completed_admin_deleted_and_secret_rotated")
    return True
