"""Routes HTTP de recherche des communes par coordonnées GPS.

API -> repository -> PostgreSQL/PostGIS -> schéma Pydantic.
Le repository fait le calcul géographique ; cette route gère uniquement les
paramètres, les codes HTTP et le format de la réponse.
"""

from fastapi import APIRouter, HTTPException, Query, status

from app.repositories.commune import get_commune
from app.schemas.commune import CommuneResponse


router = APIRouter(prefix="/communes", tags=["communes"])


@router.get(
    "/",
    response_model=CommuneResponse,
    summary="Trouver la commune d'un point",
)
def get_commune_from_coordinates(
    lon: float = Query(ge=-180, le=180, allow_inf_nan=False),
    lat: float = Query(ge=-90, le=90, allow_inf_nan=False),
):
    """Renvoie le code INSEE et le nom de la commune contenant ce point.

    IMPORTANT : ``lon`` = longitude (est/ouest), ``lat`` = latitude (nord/sud).
    Les validations FastAPI retournent automatiquement 422 pour un paramètre
    manquant, non numérique, hors bornes ou non fini (NaN/Infinity).
    """
    commune = get_commune(lon=lon, lat=lat)

    if commune is None:
        # 404 : le point ne correspond à aucune commune de la base actuelle.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commune not found",
        )

    # Les clés SQL (code, nom) deviennent celles du contrat public de l'API.
    return {
        "commune_code": commune["code"],
        "commune_name": commune["nom"],
    }
