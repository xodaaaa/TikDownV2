from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    SECRET_KEY: str = ""
    FERNET_KEY: str = ""
    DATABASE_PATH: str = "/app/data/tikdown.db"
    SCHEDULER_DB_PATH: str = "/app/data/scheduler.db"
    VIDEOS_DIR: str = "/app/data/videos"
    BACKUPS_DIR: str = "/app/data/backups"
    LOG_LEVEL: str = "INFO"
    MONITOR_AUTOSTART: bool = False
    FORCE_RESET: bool = False
    ENABLE_API_DOCS: bool = False
    CORS_ORIGINS: str = "http://localhost:5173"

    # Monitor
    MONITOR_INTERVAL_MINUTES: int = 10
    MIN_MONITOR_INTERVAL_MINUTES: int = 5
    MAX_CONCURRENT_DOWNLOADS: int = 2
    MIN_DELAY_SECONDS: int = 10
    MAX_DELAY_SECONDS: int = 60
    BACKOFF_MAX_SECONDS: int = 1800
    CIRCUIT_BREAKER_FAILS: int = 5
    DOWNLOAD_TIMEOUT_SECONDS: int = 600
    CHECK_NOW_THROTTLE_SECONDS: int = 30
    PROFILE_REFRESH_HOURS: int = 48
    DISK_MONITOR_INTERVAL_SECONDS: int = 300
    NETWORK_PROBE_INTERVAL: int = 30
    NETWORK_OFFLINE_THRESHOLD: int = 3
    NETWORK_PROBE_URL: str = "https://1.1.1.1"
    EVENTS_RETENTION_DAYS: int = 7
    LOG_BUFFER_SIZE: int = 1000

    # Backfill
    BACKFILL_DELAY_MIN: int = 5
    BACKFILL_DELAY_MAX: int = 15
    BACKFILL_PAUSE_EVERY_N: int = 50
    BACKFILL_LONG_PAUSE_MIN: int = 60
    BACKFILL_LONG_PAUSE_MAX: int = 120

    # Notificaciones
    ENABLE_EXTERNAL_NOTIFICATIONS: bool = False
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    TELEGRAM_BOT_MODE: str = "notifications"
    TELEGRAM_POLLING_INTERVAL: int = 3

    @property
    def data_dir(self) -> Path:
        return Path(self.DATABASE_PATH).parent

    @property
    def videos_path(self) -> Path:
        return Path(self.VIDEOS_DIR)

    @property
    def backups_path(self) -> Path:
        return Path(self.BACKUPS_DIR)

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
