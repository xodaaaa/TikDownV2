from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.video import Video


class VideosService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_videos(
        self,
        account_id: str | None = None,
        status_filter: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Video]:
        stmt = select(Video).order_by(Video.created_at.desc())
        if account_id:
            stmt = stmt.where(Video.monitored_account_id == account_id)
        if status_filter:
            stmt = stmt.where(Video.status == status_filter)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_video(self, video_id: str) -> Video | None:
        return await self.db.get(Video, video_id)

    async def delete_video(self, video_id: str) -> bool:
        video = await self.get_video(video_id)
        if not video:
            return False
        if video.file_path:
            Path(video.file_path).unlink(missing_ok=True)
        if video.thumbnail_path:
            Path(video.thumbnail_path).unlink(missing_ok=True)
        await self.db.delete(video)
        await self.db.commit()
        return True
