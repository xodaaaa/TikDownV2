FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_24.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g pnpm@11.9 \
    && corepack enable

COPY backend/pyproject.toml backend/uv.lock /app/backend/
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml /app/frontend/

COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

RUN ln -sf /app/backend/alembic /app/alembic

RUN cd /app/frontend && pnpm install --frozen-lockfile && pnpm build

RUN pip install uv && cd /app/backend && uv sync --frozen

RUN uv run --project /app/backend python -c "import yt_dlp"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=60s \
    CMD curl -f http://localhost:8000/api/system/health || exit 1

COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

ENTRYPOINT ["/app/docker-entrypoint.sh"]
