#!/bin/bash
set -e

export PYTHONPATH=/app/backend

UV="uv run --project /app/backend"

echo "Running alembic migrations..."
$UV alembic -c /app/backend/alembic.ini upgrade head

echo "Cleaning orphan scheduler jobs..."
uv run --project /app/backend python << 'EOF'
import asyncio
import sqlalchemy.exc
from src.db.session import scheduler_engine

async def clean():
    from sqlalchemy import text
    async with scheduler_engine.begin() as conn:
        try:
            await conn.execute(text("DELETE FROM apscheduler_jobs"))
        except sqlalchemy.exc.OperationalError:
            pass

asyncio.run(clean())
EOF

echo "Starting TikDown..."
exec uv run --project /app/backend uvicorn src.main:app \
  --host 0.0.0.0 \
  --port 8000
