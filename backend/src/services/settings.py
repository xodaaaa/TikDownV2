import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.setting import AppSetting

logger = structlog.get_logger("tikdown.services.settings")


class SettingsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self, key: str, default: any = None) -> any:
        setting = await self.db.get(AppSetting, key)
        if setting is None:
            return default
        return setting.value

    async def set(self, key: str, value: any) -> AppSetting:
        setting = await self.db.get(AppSetting, key)
        if setting:
            setting.value = value
        else:
            setting = AppSetting(key=key, value=value)
            self.db.add(setting)
        await self.db.commit()
        await self.db.refresh(setting)
        return setting

    async def get_all(self) -> dict:
        result = await self.db.execute(select(AppSetting))
        settings = result.scalars().all()
        return {s.key: s.value for s in settings}

    async def delete(self, key: str) -> bool:
        setting = await self.db.get(AppSetting, key)
        if not setting:
            return False
        await self.db.delete(setting)
        await self.db.commit()
        return True
