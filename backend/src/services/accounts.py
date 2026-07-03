import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.monitored_account import MonitoredAccount

logger = structlog.get_logger("tikdown.services.accounts")


class AccountsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_accounts(
        self, enabled: bool | None = None, status_filter: str | None = None
    ) -> list[MonitoredAccount]:
        stmt = select(MonitoredAccount).order_by(MonitoredAccount.created_at.desc())
        if enabled is not None:
            stmt = stmt.where(MonitoredAccount.enabled == enabled)
        if status_filter:
            stmt = stmt.where(MonitoredAccount.status == status_filter)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_account(self, account_id: str) -> MonitoredAccount | None:
        return await self.db.get(MonitoredAccount, account_id)

    async def get_account_by_username(self, username: str) -> MonitoredAccount | None:
        result = await self.db.execute(
            select(MonitoredAccount).where(MonitoredAccount.tiktok_username == username)
        )
        return result.scalar_one_or_none()

    async def create_account(
        self, username: str, capture_mode: str = "history_and_monitor"
    ) -> MonitoredAccount:
        acc = MonitoredAccount(tiktok_username=username, capture_mode=capture_mode)
        self.db.add(acc)
        await self.db.commit()
        await self.db.refresh(acc)
        logger.info("account_created", username=username)
        return acc

    async def update_account(
        self, account_id: str, **kwargs
    ) -> MonitoredAccount | None:
        acc = await self.get_account(account_id)
        if not acc:
            return None
        for key, value in kwargs.items():
            if hasattr(acc, key):
                setattr(acc, key, value)
        await self.db.commit()
        await self.db.refresh(acc)
        return acc

    async def delete_account(self, account_id: str) -> bool:
        acc = await self.get_account(account_id)
        if not acc:
            return False
        await self.db.delete(acc)
        await self.db.commit()
        logger.info("account_deleted", username=acc.tiktok_username)
        return True
