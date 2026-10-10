"""Modèle SQLAlchemy/PostGIS d'un panneau d'affichage libre.

ATTENTION à la différence entre :
- ``status`` : état administratif/physique du *panneau* (ex. AVAILABLE) ;
- ``panel_events.event_type`` : état observé des *affiches* (ex. COVERED).

La couleur MapLibre dépend du dernier ``event_type``, pas automatiquement de
``status``. Le repository et le mapper transmettent le dernier événement.

Toute modification de la structure SQL nécessite une migration Alembic.
"""

from datetime import datetime

from geoalchemy2 import Geometry
from geoalchemy2.elements import WKBElement
from sqlalchemy import Float, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Panel(Base):
    """Un panneau physique référencé sur la carte."""

    __tablename__ = "panels"

    __table_args__ = (
        # Pour les données importées, le couple (source, source_id) identifie
        # une entrée dans le jeu de données source et évite de la réimporter.
        # PostgreSQL autorise plusieurs NULL dans source_id : cela permet
        # d'ajouter plusieurs panneaux manuels avec source_id=None.
        # ATTENTION : cela ne remplace pas le contrôle spatial à 5 mètres.
        UniqueConstraint(
            "source",
            "source_id",
            name="uq_panels_source_source_id",
        ),
    )

    # UUID4 sérialisé en chaîne, comme dans le repository add_panel().
    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    address_complement: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Coordonnées géographiques du panneau en PostGIS : (longitude, latitude).
    # L'index spatial accélère les recherches dans l'emprise de la carte.
    location: Mapped[WKBElement] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )

    # Surface en m² : le Float correspond au schéma Pydantic (float | None).
    # Vérifier séparément le type réel en base si d'anciennes migrations
    # avaient créé cette colonne en INTEGER.
    surface_m2: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Valeur par défaut appliquée par PostgreSQL en l'absence de statut.
    # Le repository add_panel() indique explicitement 'AVAILABLE'.
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="UNKNOWN",
    )

    source_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)

    # Une commune doit exister pour chaque panneau (intégrité référentielle).
    # Le type SQL est récupéré via la clé étrangère communes.code (String(5)).
    commune_code: Mapped[str] = mapped_column(
        ForeignKey("communes.code"),
        nullable=False,
    )

    # Horodatage fourni par PostgreSQL, jamais par le navigateur.
    # Le type DateTime est laissé inchangé par rapport au modèle initial.
    # Avant de le passer en timezone=True, comparer au type réel de la colonne.
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
