import tempfile
from datetime import UTC, datetime
from pathlib import Path

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.crypto import decrypt_cookie
from src.db.models.cookie import Cookie

logger = structlog.get_logger("tikdown.services.cookies")


class CookiesService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_cookies(self) -> list[Cookie]:
        result = await self.db.execute(select(Cookie).order_by(Cookie.created_at.desc()))
        return list(result.scalars().all())

    async def get_cookie(self, cookie_id: str) -> Cookie | None:
        return await self.db.get(Cookie, cookie_id)

    async def get_valid_cookies(self) -> list[Cookie]:
        result = await self.db.execute(
            select(Cookie).where(Cookie.status == "valid").order_by(Cookie.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_cookie_content(self, cookie: Cookie) -> str:
        return decrypt_cookie(cookie.encrypted_content)

    async def write_cookie_to_temp(self, cookie: Cookie) -> str:
        content = await self.get_cookie_content(cookie)
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        )
        tmp.write(content)
        tmp_path = tmp.name
        tmp.close()
        return tmp_path

    async def delete_cookie(self, cookie_id: str) -> bool:
        cookie = await self.get_cookie(cookie_id)
        if not cookie:
            return False
        await self.db.delete(cookie)
        await self.db.commit()
        logger.info("cookie_deleted", cookie_id=cookie_id)
        return True

    async def update_cookie_status(
        self, cookie_id: str, status: str
    ) -> Cookie | None:
        cookie = await self.get_cookie(cookie_id)
        if not cookie:
            return None
        cookie.status = status
        cookie.last_verified_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(cookie)
        return cookie
