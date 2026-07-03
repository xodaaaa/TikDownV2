# TikDown

Monitor y descargas automáticas de cuentas de TikTok. Aplicación web single-user con modo oscuro, notificaciones Telegram y bot bidireccional.

## Stack

- **Backend**: Python 3.12 + FastAPI + SQLAlchemy async + APScheduler + yt-dlp + curl-cffi
- **Frontend**: React 19 + Vite 8 + Tailwind CSS v4 + TanStack Query v5
- **Infra**: Docker multi-arch (linux/amd64 + linux/arm64), SQLite (WAL)

## Funcionalidades

- Monitoreo de cuentas TikTok con intervalo configurable
- Backfill de historial completo con perfil conservador anti-ban
- Reproducción de vídeos con soporte HTTP Range
- Galería con vista álbumes por cuenta
- Modo oscuro/claro
- Cifrado de cookies con Fernet
- Notificaciones Telegram salientes
- Bot de Telegram bidireccional (13 comandos)
- Healthcheck, métricas, logs en tiempo real vía SSE
- Export/import de configuración
- Backup automático de DB

## Requisitos

- Docker (para despliegue)
- Python 3.12+ y Node.js 24+ (para desarrollo)

## Desarrollo rápido

```bash
# Backend
cd backend
uv sync --extra dev
uv run uvicorn src.main:app --reload --port 8000

# Frontend (otra terminal)
cd frontend
pnpm install
pnpm dev
```

## Despliegue con Docker

```bash
cp .env.example .env
# Editar .env (SECRET_KEY, FERNET_KEY, etc.)
docker compose up -d --build
```

Acceder a `http://localhost:8000`. El primer arranque muestra el wizard de 3 pasos.

## Tests

```bash
cd backend
uv sync --extra dev
uv run pytest src/tests/ -v
```

## Licencia

Uso personal.
