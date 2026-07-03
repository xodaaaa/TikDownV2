#!/bin/bash
set -e

echo "Running alembic migrations..."
cd /app/backend
alembic upgrade head

echo "Cleaning orphan scheduler jobs..."
python -c "
import asyncio
from src.db.session import scheduler_engine
from src.config import settings
async def clean():
    from sqlalchemy import text
    async with scheduler_engine.begin() as conn:
        await conn.execute(text(\"DELETE FROM apscheduler_jobs\"))
asyncio.run(clean())
"

echo "Starting TikDown..."
exec uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --graceful-timeout 10
