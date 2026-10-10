"""Routes HTTP de création et de consultation des panneaux d'affichage.

Séparation des responsabilités :
- FastAPI valide les requêtes et renvoie les bons codes HTTP ;
- le repository accède à PostgreSQL/PostGIS ;
- le mapper fabrique le format détaillé ou GeoJSON ;
- Pydantic valide les réponses avant de les transmettre au navigateur.
"""

from fastapi import APIRouter, HTTPException, Path, Query, status

from app.mappers.panel import panel_to_response, panels_to_feature_collection
from app.repositories.panel import add_panel, get_panel, get_panels_in_bbox
from app.schemas.panel import PanelCreate, PanelFeatureCollection, PanelResponse


router = APIRouter(prefix="/panels", tags=["panels"])


@router.post(
    "/",
    response_model=PanelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un panneau",
)
def create_panel(panel: PanelCreate):
    """Ajoute un panneau et renvoie sa fiche détaillée.

    Le repository peut refuser la création dans deux situations métier :
    - panneau déjà présent à moins de 5 m : HTTP 409 (conflit) ;
    - aucun territoire communal correspondant : HTTP 422 (point non valide).

    TODO : remplacer à terme les messages ValueError du repository par des
    exceptions métier typées (DuplicatePanelError, CommuneNotFoundError).
    La comparaison des messages ci-dessous conserve la compatibilité avec
    les repositories déjà corrigés, sans les modifier dans cette étape.
    """
    try:
        created_panel = add_panel(
            lon=panel.longitude,
            lat=panel.latitude,
            address=panel.address,
            address_complement=panel.address_complement,
            surface_m2=panel.surface_m2,
        )
    except ValueError as exc:
        error = str(exc)
        if error.startswith("Panel already exists nearby"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error,
            ) from exc
        if error.startswith("No commune found for coordinates"):
            raise HTTPException(
                status_code=422,  # Validation métier : contenu non traitable
                detail=error,
            ) from exc
        # Ne pas masquer un éventuel bug du repository avec un faux 422.
        raise

    # POST et GET détaillé partagent le même format de sortie.
    return panel_to_response(created_panel)


@router.get(
    "/",
    response_model=PanelFeatureCollection,
    summary="Lister les panneaux visibles sur la carte",
)
def read_panels(
    min_lon: float = Query(ge=-180, le=180, allow_inf_nan=False),
    min_lat: float = Query(ge=-90, le=90, allow_inf_nan=False),
    max_lon: float = Query(ge=-180, le=180, allow_inf_nan=False),
    max_lat: float = Query(ge=-90, le=90, allow_inf_nan=False),
):
    """Retourne une FeatureCollection GeoJSON limitée à une emprise WGS84.

    MapLibre fournit les bornes de la carte dans cet ordre :
      (min_lon, min_lat) = (ouest, sud)
      (max_lon, max_lat) = (est, nord)

    Les bornes enroulées autour de l'antiméridien ne sont pas gérées par cette
    API pour le moment. Pour une carte française, ce cas est généralement
    sans incidence ; il faudra l'ajouter si l'application devient mondiale.
    """
    if min_lon > max_lon or min_lat > max_lat:
        raise HTTPException(
            status_code=422,  # Validation métier : contenu non traitable
            detail="Invalid bounding box: min_lon <= max_lon and min_lat <= max_lat are required",
        )

    panels = get_panels_in_bbox(
        min_lon=min_lon,
        min_lat=min_lat,
        max_lon=max_lon,
        max_lat=max_lat,
    )

    # Le mapper place latest_event_type dans les propriétés GeoJSON.
    # C'est ce champ que MapLibre doit utiliser pour les couleurs.
    return panels_to_feature_collection(panels)


@router.get(
    "/{panel_id}",
    response_model=PanelResponse,
    summary="Consulter un panneau",
)
def read_panel(
    panel_id: str = Path(description="Identifiant d'un panneau en base"),
):
    """Renvoie un panneau précis, ou 404 s'il n'existe pas.

    Le type de l'identifiant reste ``str`` : la colonne de la base est textuelle
    et les imports peuvent contenir d'autres identifiants que des UUID4.
    Les valeurs sont passées au SQL comme paramètres, jamais concaténées.
    """
    panel = get_panel(panel_id)
    if panel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Panel not found",
        )

    return panel_to_response(panel)
