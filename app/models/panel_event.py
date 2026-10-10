"""Modèle SQLAlchemy d'un événement de panneau d'affichage.

Les événements sont *ajoutés* à un historique et ne remplacent pas les
anciens événements. Leur type (COVERED, EMPTY, VISIBLE, etc.) est contrôlé
par le schéma Pydantic et le repository, sans contrainte CHECK SQL ici.

Le dernier événement par panneau est lu par le repository ; le mapper
l'inclut dans les propriétés GeoJSON pour les couleurs MapLibre.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PanelEvent(Base):
    """Signalement horodaté rattaché à un panneau existant."""

    __tablename__ = "panel_events"

    __table_args__ = (
        # Accélère la lecture de l'historique et du dernier événement
        # (filtrage par panel_id, tri par created_at).
        # L'ordre entre événements ayant exactement la même date est départagé
        # dans les requêtes SQL par event_id ; l'index actuel est conservé
        # pour ne pas déclencher une migration inutile.
        Index("idx_panel_events_panel_created_at", "panel_id", "created_at"),
    )

    # Identifiant unique du signalement (UUID4 sérialisé en chaîne).
    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # La clé étrangère empêche l'ajout d'un événement pour un panneau absent.
    # Ne fournit pas à elle seule une réponse HTTP 404 (à gérer dans l'API).
    panel_id: Mapped[str] = mapped_column(
        ForeignKey("panels.id"),
        nullable=False,
    )

    # Le serveur PostgreSQL remplit la date à l'insertion.
    # timestamptz côté SQLAlchemy ; vérifier le type réel via les migrations.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Valeurs autorisées dans app.schemas.panel_event.EventType ;
    # source unique de validation métier, pas d'ENUM en base à ce stade.
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)

    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_id: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Dans ce modèle, la source est obligatoire ; le repository utilise
    # 'user' si l'API ne lui passe aucune provenance.
    source: Mapped[str] = mapped_column(String(100), nullable=False)
