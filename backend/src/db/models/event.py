import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Index, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(
        Text, primary_key=True, default=lambda: uuid.uuid4().hex
    )
    type: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    __table_args__ = (Index("idx_events_created_at", "created_at"),)
