"""Transformations des panneaux du repository vers les réponses de l'API.

Le repository renvoie des lignes SQL sous forme de dictionnaires avec, entre
 autres, ``longitude`` et ``latitude``. Ce module les convertit en :

- réponse détaillée : ``PanelResponse`` (champ ``location``) ;
- GeoJSON : ``PanelFeatureCollection`` utilisé par MapLibre.

Important : les mappers ne consultent PAS la base de données. Les requêtes
PostGIS et la récupération du dernier événement sont faites au repository.
"""

from typing import Any, Mapping


def _point_geometry(panel: Mapping[str, Any]) -> dict[str, Any]:
    """Construit un Point GeoJSON 2D : [longitude, latitude], JAMAIS l'inverse.

    Les deux champs sont obligatoires dans les résultats des repositories.
    Un KeyError ici signale donc un défaut du SELECT ou du contrat de données.
    Les coordonnées sont validées à la sortie par les schémas Pydantic.
    """
    return {
        "type": "Point",
        "coordinates": [panel["longitude"], panel["latitude"]],
    }


def panel_to_response(panel: Mapping[str, Any]) -> dict[str, Any]:
    """Convertit une ligne de panneau en données pour ``PanelResponse``.

    Usage : réponse au GET /panels/{id} ou après le POST /panels/.
    On conserve la distinction entre ``status`` (disponibilité physique du
    panneau) et les événements d'affichage (historisés ailleurs).

    Les champs du modèle Pydantic ``PanelResponse`` sont conservés à l'identique.
    """
    return {
        "id": panel["id"],
        "address": panel["address"],
        "address_complement": panel["address_complement"],
        "location": _point_geometry(panel),
        "surface_m2": panel["surface_m2"],
        "status": panel["status"],
        "source_id": panel["source_id"],
        "source": panel["source"],
        "commune_code": panel["commune_code"],
        "created_at": panel["created_at"],
    }


def panel_to_feature(panel: Mapping[str, Any]) -> dict[str, Any]:
    """Convertit un panneau en ``Feature`` GeoJSON pour la carte MapLibre.

    ``latest_event_type`` détermine la couleur d'un panneau. Le repository
    extrait normalement ce champ par LEFT JOIN LATERAL sur ``panel_events``.

    Seuls les champs du *dernier événement* utilisent ``get()`` : un panneau
    créé par ``add_panel()`` n'a pas encore forcément de telles clés, et un
    panneau sans événement doit renvoyer ``null``. Les autres clés restent
    obligatoires pour révéler rapidement une incohérence repository/mapper.

    À vérifier côté JS : la propriété ``id`` est utilisée par ``promoteId``
    si MapLibre mémorise un événement récent dans le feature-state.
    """
    return {
        "type": "Feature",
        "geometry": _point_geometry(panel),
        "properties": {
            "id": panel["id"],
            "address": panel["address"],
            "address_complement": panel["address_complement"],
            "surface_m2": panel["surface_m2"],
            "status": panel["status"],
            "latest_event_type": panel.get("latest_event_type"),
            "latest_event_created_at": panel.get("latest_event_created_at"),
            "commune_code": panel["commune_code"],
        },
    }


def panels_to_feature_collection(
    panels: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """Construit un ``FeatureCollection`` GeoJSON, y compris pour une liste vide.

    Usage : résultat de GET /panels/ pour l'emprise courante de la carte.
    La validation de sortie est prise en charge par ``PanelFeatureCollection``.
    """
    return {
        "type": "FeatureCollection",
        "features": [panel_to_feature(panel) for panel in panels],
    }
