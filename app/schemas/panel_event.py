"""Schémas de création et de lecture des événements d'un panneau."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


# IMPORTANT : ces valeurs sont échangées telles quelles entre l'API et le JS.
# Un événement décrit un signalement, pas le statut d'existence du panneau
# stocké dans panels.status (par exemple « AVAILABLE »).
# Si cette liste évolue, mettre aussi à jour les choix/couleurs du frontend.
EventType = Literal[
    "POSTER_ADDED",        # Une nouvelle affiche a été collée.
    "VISIBLE",             # L'affiche est visible.
    "PARTIALLY_COVERED",   # L'affiche est partiellement recouverte.
    "COVERED",             # L'affiche est recouverte.
    "EMPTY",               # Le panneau ne porte plus d'affiche.
    "POSTER_REMOVED",      # Un retrait d'affiche a été signalé.
]


class PanelEventCreate(BaseModel):
    """Corps envoyé à POST /panels/{panel_id}/events/.

    L'identifiant du panneau est dans l'URL ; la date et la provenance doivent
    être déterminées par le serveur et non imposées par le client.
    """

    event_type: EventType
    comment: str | None = None  # Facultatif ; une chaîne vide reste acceptée.


class PanelEventResponse(BaseModel):
    """Représentation d'un événement enregistré en base de données."""

    event_id: str
    panel_id: str
    created_at: datetime
    event_type: EventType
    comment: str | None
    source_id: str | None
    source: str | None
