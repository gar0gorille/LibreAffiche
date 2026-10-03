from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from geoalchemy2 import Geometry

from app.database import Base


class Commune(Base):
    __tablename__ = "communes"

    code: Mapped[str] = mapped_column(
        String(5),
        primary_key=True,
    )

    nom: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    departement: Mapped[str | None] = mapped_column(
        String(3),
    )

    region: Mapped[str | None] = mapped_column(
        String(3),
    )

    epci: Mapped[str | None] = mapped_column(
        String(20),
    )

    geometry = mapped_column(
        Geometry(
            geometry_type="MULTIPOLYGON",
            srid=4326,
            spatial_index=True,
        ),
        nullable=False,
    )
