import hashlib
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.video import Video


class IntegrityChecker:
    @staticmethod
    def calculate_hash(file_path: str) -> str:
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def verify_file(file_path: str, expected_hash: str) -> bool:
        if not Path(file_path).exists():
            return False
        try:
            actual = IntegrityChecker.calculate_hash(file_path)
            return actual == expected_hash
        except (OSError, IOError):
            return False

    @staticmethod
    async def check_last_video(account_id: str, session: AsyncSession) -> bool:
        stmt = (
            select(Video)
            .where(
                Video.monitored_account_id == account_id,
                Video.status == "downloaded",
                Video.file_hash.isnot(None),
            )
            .order_by(Video.downloaded_at.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        video = result.scalar_one_or_none()
        if video is None or not video.file_path or not video.file_hash:
            return True
        return IntegrityChecker.verify_file(video.file_path, video.file_hash)
