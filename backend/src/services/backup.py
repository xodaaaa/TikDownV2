from datetime import UTC, datetime
from pathlib import Path

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings

logger = structlog.get_logger("tikdown.services.backup")


class BackupService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_backup(self) -> Path:
        backup_dir = Path(settings.BACKUPS_DIR)
        backup_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now(UTC).strftime("%Y%m%d")
        backup_path = backup_dir / f"tikdown_{date_str}.db"

        db_path = Path(settings.DATABASE_PATH)
        if not db_path.exists():
            raise FileNotFoundError(f"Database not found at {db_path}")

        await self.db.execute(text(f"VACUUM INTO '{backup_path}'"))
        logger.info("backup_created", path=str(backup_path))
        return backup_path

    async def cleanup_old_backups(self, keep: int = 7) -> int:
        backup_dir = Path(settings.BACKUPS_DIR)
        if not backup_dir.exists():
            return 0
        backups = sorted(backup_dir.glob("tikdown_*.db"), reverse=True)
        if len(backups) <= keep:
            return 0
        removed = 0
        for old in backups[keep:]:
            old.unlink(missing_ok=True)
            removed += 1
        if removed:
            logger.info("backups_cleaned", removed=removed, keep=keep)
        return removed
