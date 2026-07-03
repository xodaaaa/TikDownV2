import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, CheckConstraint, DateTime, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models.video import Video


class MonitoredAccount(Base):
    __tablename__ = "monitored_accounts"

    id: Mapped[str] = mapped_column(
        Text, primary_key=True, default=lambda: uuid.uuid4().hex
    )
    tiktok_username: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(default=True)
    status: Mapped[str] = mapped_column(Text, default="ok")
    capture_mode: Mapped[str] = mapped_column(Text, default="history_and_monitor")
    last_check_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_video_timestamp: Mapped[int | None] = mapped_column(nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(default=0)
    options: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_local_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    follower_count: Mapped[int | None] = mapped_column(nullable=True)
    following_count: Mapped[int | None] = mapped_column(nullable=True)
    total_likes: Mapped[int | None] = mapped_column(nullable=True)
    video_count: Mapped[int | None] = mapped_column(nullable=True)
    profile_last_refreshed: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    backfill_status: Mapped[str] = mapped_column(Text, default="idle")
    backfill_cursor: Mapped[str | None] = mapped_column(Text, nullable=True)
    backfill_total: Mapped[int | None] = mapped_column(nullable=True)
    backfill_done: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    videos: Mapped[list["Video"]] = relationship(
        back_populates="monitored_account", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('ok','needs_review','paused')",
            name="ck_monitored_accounts_status",
        ),
        CheckConstraint(
            "capture_mode IN ('history_and_monitor','monitor_only')",
            name="ck_monitored_accounts_capture_mode",
        ),
        CheckConstraint(
            "backfill_status IN ('idle','backfilling','paused','completed','cancelled')",
            name="ck_monitored_accounts_backfill_status",
        ),
    )
