import asyncio
import json
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import SessionDep
from src.db.models.event import Event
from src.db.session import get_db

logger = structlog.get_logger("tikdown.routes.events")

router = APIRouter(prefix="/api/events", tags=["events"], dependencies=[SessionDep])

_event_queue: asyncio.Queue = asyncio.Queue()


async def push_event(event_type: str, payload: dict) -> None:
    data = json.dumps({"type": event_type, "payload": payload})
    await _event_queue.put(data)


async def push_event_to_sse(event_type: str, payload: dict) -> None:
    await push_event(event_type, payload)


@router.get("")
async def event_stream(request: Request) -> None:
    async def _generate():
        heartbeat_interval = 30
        while True:
            if await request.is_disconnected():
                break
            try:
                data = await asyncio.wait_for(_event_queue.get(), timeout=heartbeat_interval)
                yield f"data: {data}\n\n"
            except asyncio.TimeoutError:
                yield "event: ping\ndata: {}\n\n"

    from fastapi.responses import StreamingResponse

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history")
async def event_history(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(50, ge=1, le=200),
    level: str | None = Query(None),
) -> list[dict]:
    stmt = select(Event).order_by(desc(Event.created_at)).limit(limit)
    if level:
        pass
    result = await db.execute(stmt)
    events = result.scalars().all()
    return [
        {
            "id": e.id,
            "type": e.type,
            "payload": e.payload,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]
