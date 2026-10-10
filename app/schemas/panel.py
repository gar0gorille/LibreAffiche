"""Schémas Pydantic des panneaux et de leur représentation GeoJSON.

Le frontend MapLibre consomme principalement `PanelFeatureCollection`.
Les noms des champs constituent un contrat entre le backend et le JS :
les modifier nécessite également de modifier les mappers et le frontend.
"""

from datetime import datetime
from math import isfinite
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.panel_event import EventType


class PointGeometry(BaseModel):
    """Géométrie GeoJSON Point, toujours au format [longitude, latitude]."""

    type: Literal["Point"] = "Point"
    # GeoJSON Point 2D : exactement 2 coordonnées, dans cet ordre.
    coordinates: list[float] = Field(min_length=2, max_length=2)

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(cls, value: list[float]) -> list[float]:
        """Refuse les points hors WGS84 ou contenant NaN / l'infini.

        En cas d'erreur sur une réponse API, vérifier d'abord le mapper qui
        transforme la géométrie PostGIS en [longitude, latitude].
        """
        lon, lat = value
        if not (isfinite(lon) and isfinite(lat)):
            raise ValueError("Les coordonnées doivent être des nombres finis")
        if not (-180 <= lon <= 180):
            raise ValueError("La longitude doit être comprise entre -180 et 180")
        if not (-90 <= lat <= 90):
            raise ValueError("La latitude doit être comprise entre -90 et 90")
        return value


class PanelProperties(BaseModel):
    """Attributs d'un panneau dans `Feature.properties` (GeoJSON)."""

    id: str  # Identifiant du panneau ; utilisé aussi par MapLibre (promoteId).
    address: str | None
    address_complement: str | None
    surface_m2: float | None

    # Statut historique / d'existence du panneau en base.
    # NE PAS confondre avec `latest_event_type`, qui pilote la couleur de
    # l'affichage selon le dernier signalement.
    status: str

    # Ces champs sont facultatifs pour les panneaux sans signalement.
    # Attention : les déclarer ici ne suffit pas à les remplir !
    # Le repository + le mapper doivent récupérer le dernier événement.
    latest_event_type: EventType | None = None
    latest_event_created_at: datetime | None = None

    commune_code: str


class PanelFeature(BaseModel):
    """Une entité GeoJSON de type Feature."""

    type: Literal["Feature"] = "Feature"
    geometry: PointGeometry
    properties: PanelProperties


class PanelFeatureCollection(BaseModel):
    """Réponse GeoJSON de GET /panels/ pour l'emprise de la carte."""

    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[PanelFeature]  # [] est valide si aucun panneau n'est trouvé.


class PanelCreate(BaseModel):
    """Données envoyées lors de l'ajout d'un panneau.

    La commune est déduite des coordonnées côté serveur ; les autres champs
    (id, statut, source, date) sont déterminés côté backend.
    """

    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)

    address: str | None = None
    address_complement: str | None = None
    # La surface saisie doit être positive. Une valeur absente est autorisée.
    surface_m2: float | None = Field(default=None, gt=0, allow_inf_nan=False)


class PanelResponse(BaseModel):
    """Réponse détaillée d'un panneau, distincte du format GeoJSON Feature."""

    id: str

    address: str | None
    address_complement: str | None

    location: PointGeometry

    surface_m2: float | None
    status: str  # Statut du panneau en base, pas forcément celui du dernier event.

    source_id: str | None
    source: str

    commune_code: str
    created_at: datetime  # Le repository/mapper doit fournir ce champ.
