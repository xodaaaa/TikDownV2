import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models.monitored_account import MonitoredAccount


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[str] = mapped_column(
        Text, primary_key=True, default=lambda: uuid.uuid4().hex
    )
    monitored_account_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("monitored_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    tiktok_id: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, default="")
    upload_date: Mapped[str | None] = mapped_column(Text, nullable=True)
    upload_timestamp: Mapped[int | None] = mapped_column(nullable=True)
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    thumbnail_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration: Mapped[int | None] = mapped_column(nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_size: Mapped[int | None] = mapped_column(nullable=True)
    file_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    likes: Mapped[int | None] = mapped_column(nullable=True)
    views: Mapped[int | None] = mapped_column(nullable=True)
    downloaded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(Text, default="queued")
    error_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_kind: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    monitored_account: Mapped["MonitoredAccount"] = relationship(
        back_populates="videos"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('queued','downloading','downloaded','failed')",
            name="ck_videos_status",
        ),
        CheckConstraint(
            "error_kind IN ('auth','rate_limit','ip_block','network','not_found','unknown')",
            name="ck_videos_error_kind",
        ),
        Index("idx_videos_account_id", "monitored_account_id"),
        Index("idx_videos_status", "status"),
        Index("idx_videos_downloaded_at", "downloaded_at"),
    )
