import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, LargeBinary, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class Cookie(Base):
    __tablename__ = "cookies"

    id: Mapped[str] = mapped_column(
        Text, primary_key=True, default=lambda: uuid.uuid4().hex
    )
    original_format: Mapped[str] = mapped_column(Text, nullable=False)
    encrypted_content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    status: Mapped[str] = mapped_column(Text, default="unverified")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    __table_args__ = (
        CheckConstraint(
            "original_format IN ('txt','json')", name="ck_cookies_original_format"
        ),
        CheckConstraint(
            "status IN ('valid','unverified','invalid','expired')",
            name="ck_cookies_status",
        ),
    )
