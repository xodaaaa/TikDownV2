from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import (
    AuthResponse,
    check_needs_setup,
    delete_session_cookie,
    get_secret_key,
    hash_password,
    set_session_cookie,
    verify_password,
)
from src.core.crypto import get_secret_key as get_crypto_secret_key
from src.db.models.admin import Admin
from src.db.models.setting import AppSetting
from src.db.session import get_db

logger = structlog.get_logger("tikdown.routes.auth")

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SetupRequest(BaseModel):
    password: str


class SetupResponse(BaseModel):
    success: bool
    needs_setup: bool


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    success: bool
    authenticated: bool
    needs_setup: bool


@router.get("/status", response_model=AuthResponse)
async def auth_status(db: Annotated[AsyncSession, Depends(get_db)]) -> AuthResponse:
    needs = await check_needs_setup(db)
    return AuthResponse(authenticated=not needs, needs_setup=needs)


@router.post("/setup", response_model=SetupResponse)
async def auth_setup(
    body: SetupRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SetupResponse:
    needs = await check_needs_setup(db)
    if not needs:
        raise HTTPException(status_code=400, detail="Admin already configured")

    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    pw_hash = hash_password(body.password)
    admin = Admin(password_hash=pw_hash)
    db.add(admin)
    await db.commit()

    secret_key = get_crypto_secret_key()
    set_session_cookie(response, secret_key)

    logger.info("admin_setup_completed")
    return SetupResponse(success=True, needs_setup=False)


@router.post("/login", response_model=LoginResponse)
async def auth_login(
    body: LoginRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LoginResponse:
    needs = await check_needs_setup(db)
    if needs:
        raise HTTPException(status_code=400, detail="Admin not configured, please run setup first")

    result = await db.execute(select(Admin).limit(1))
    admin = result.scalar_one_or_none()
    if admin is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(body.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    secret_key = get_crypto_secret_key()
    set_session_cookie(response, secret_key)

    logger.info("admin_login_success")
    return LoginResponse(success=True, authenticated=True, needs_setup=False)


@router.post("/logout")
async def auth_logout(response: Response) -> dict:
    delete_session_cookie(response)
    logger.info("admin_logout")
    return {"success": True}
