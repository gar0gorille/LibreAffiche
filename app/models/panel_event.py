from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PanelEvent(Base):
    __tablename__ = "panel_events"

    __table_args__ = (
        Index(
            "idx_panel_events_panel_created_at",
            "panel_id",
            "created_at",
        ),
    )

    event_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    panel_id: Mapped[str] = mapped_column(
        ForeignKey("panels.id"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    source_id: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
