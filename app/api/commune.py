from fastapi import APIRouter, HTTPException, Query

from app.repositories.commune import get_commune
from app.schemas.commune import CommuneResponse


router = APIRouter(
    prefix="/communes",
    tags=["communes"],
)


@router.get(
    "/",
    response_model=CommuneResponse,
)
def get_commune_from_coordinates(
    lon: float = Query(ge=-180, le=180),
    lat: float = Query(ge=-90, le=90),
):
    commune = get_commune(
        lon=lon,
        lat=lat,
    )

    if commune is None:
        raise HTTPException(
            status_code=404,
            detail="Commune not found",
        )

    return {
        "commune_code": commune["code"],
        "commune_name": commune["nom"],
    }