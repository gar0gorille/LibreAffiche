from datetime import datetime

from sqlalchemy import (
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry

from app.database import Base


class Panel(Base):
    __tablename__ = "panels"

    __table_args__ = (
        UniqueConstraint(
            "source",
            "source_id",
            name="uq_panels_source_source_id",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    address: Mapped[str | None] = mapped_column(Text)

    address_complement: Mapped[str | None] = mapped_column(Text)

    location = mapped_column(
        Geometry(
            geometry_type="POINT",
            srid=4326,
            spatial_index=True,
        ),
        nullable=False,
    )

    surface_m2: Mapped[float | None] = mapped_column(Float)

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="UNKNOWN",
    )

    source_id: Mapped[str | None] = mapped_column(Text)

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    commune_code: Mapped[str] = mapped_column(
        ForeignKey("communes.code"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
