import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, Response, StreamingResponse
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from src.config import settings
from src.core.auth import SessionDep
from src.db.models.video import Video
from src.db.session import get_db

logger = structlog.get_logger("tikdown.routes.videos")

router = APIRouter(prefix="/api/videos", tags=["videos"], dependencies=[SessionDep])


async def _get_video_or_404(video_id: str, db: AsyncSession) -> Video:
    video = await db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@router.get("")
async def list_videos(
    db: Annotated[AsyncSession, Depends(get_db)],
    account_id: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    stmt = select(Video).order_by(Video.created_at.desc())
    if account_id:
        stmt = stmt.where(Video.monitored_account_id == account_id)
    if status_filter:
        stmt = stmt.where(Video.status == status_filter)
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    videos = result.scalars().all()
    return {
        "videos": [
            {
                "id": v.id,
                "monitored_account_id": v.monitored_account_id,
                "tiktok_id": v.tiktok_id,
                "title": v.title,
                "upload_date": v.upload_date,
                "upload_timestamp": v.upload_timestamp,
                "file_path": v.file_path,
                "thumbnail_path": v.thumbnail_path,
                "duration": v.duration,
                "file_size": v.file_size,
                "file_hash": v.file_hash,
                "likes": v.likes,
                "views": v.views,
                "downloaded_at": v.downloaded_at.isoformat() if v.downloaded_at else None,
                "status": v.status,
                "error_text": v.error_text,
                "error_kind": v.error_kind,
                "retry_count": v.retry_count,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in videos
        ],
        "total": len(videos),
        "offset": offset,
        "limit": limit,
    }


@router.get("/{video_id}")
async def get_video(
    video_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    video = await _get_video_or_404(video_id, db)
    return {
        "id": video.id,
        "monitored_account_id": video.monitored_account_id,
        "tiktok_id": video.tiktok_id,
        "title": video.title,
        "upload_date": video.upload_date,
        "upload_timestamp": video.upload_timestamp,
        "file_path": video.file_path,
        "thumbnail_path": video.thumbnail_path,
        "duration": video.duration,
        "description": video.description,
        "file_size": video.file_size,
        "file_hash": video.file_hash,
        "likes": video.likes,
        "views": video.views,
        "downloaded_at": video.downloaded_at.isoformat() if video.downloaded_at else None,
        "status": video.status,
        "error_text": video.error_text,
        "error_kind": video.error_kind,
        "retry_count": video.retry_count,
        "created_at": video.created_at.isoformat() if video.created_at else None,
    }


@router.get("/{video_id}/file")
async def serve_video_file(
    video_id: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    video = await _get_video_or_404(video_id, db)
    if not video.file_path:
        raise HTTPException(status_code=404, detail="Video file not found on disk")
    file_path = Path(video.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found on disk")

    file_size = file_path.stat().st_size
    range_header = request.headers.get("range")

    if not range_header:
        return FileResponse(
            str(file_path),
            media_type="video/mp4",
            filename=file_path.name,
        )

    start_str = range_header.replace("bytes=", "").split("-")
    start = int(start_str[0]) if start_str[0] else 0
    end = int(start_str[1]) if len(start_str) > 1 and start_str[1] else file_size - 1

    if start >= file_size:
        return Response(status_code=416, content="Range Not Satisfiable")

    chunk_size = end - start + 1

    async def _stream_chunk():
        with open(file_path, "rb") as f:
            f.seek(start)
            remaining = chunk_size
            while remaining > 0:
                read_size = min(8192, remaining)
                data = f.read(read_size)
                if not data:
                    break
                remaining -= len(data)
                yield data

    return StreamingResponse(
        _stream_chunk(),
        status_code=206,
        media_type="video/mp4",
        headers={
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Content-Length": str(chunk_size),
            "Accept-Ranges": "bytes",
        },
    )


@router.get("/{video_id}/thumbnail")
async def serve_thumbnail(
    video_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    video = await _get_video_or_404(video_id, db)
    if not video.thumbnail_path:
        raise HTTPException(status_code=404, detail="No thumbnail available")
    thumb_path = Path(video.thumbnail_path)
    if not thumb_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail file not found")
    return FileResponse(str(thumb_path))


@router.delete("/{video_id}", status_code=204)
async def delete_video(
    video_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    video = await _get_video_or_404(video_id, db)
    if video.file_path:
        Path(video.file_path).unlink(missing_ok=True)
    if video.thumbnail_path:
        Path(video.thumbnail_path).unlink(missing_ok=True)
    await db.delete(video)
    await db.commit()
    logger.info("video_deleted", tiktok_id=video.tiktok_id)


@router.post("/{video_id}/redownload", response_model=dict)
async def redownload_video(
    video_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    video = await _get_video_or_404(video_id, db)
    if video.file_path:
        Path(video.file_path).unlink(missing_ok=True)
    if video.thumbnail_path:
        Path(video.thumbnail_path).unlink(missing_ok=True)
    video.status = "queued"
    video.file_path = None
    video.thumbnail_path = None
    video.file_hash = None
    video.file_size = None
    video.error_text = None
    video.error_kind = None
    video.retry_count = 0
    await db.commit()
    logger.info("video_redownload_queued", tiktok_id=video.tiktok_id)
    return {"message": "Video queued for redownload", "video_id": video_id}
