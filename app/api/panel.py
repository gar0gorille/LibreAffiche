from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.repositories.panel import (
    add_panel,
    get_panel,
    get_panels_in_bbox,
)
from app.schemas.panel import (
    PanelCreate,
    PanelFeatureCollection,
    PanelResponse,
)
from app.mappers.panel import (
    panel_to_response,
    panels_to_feature_collection,
)


router = APIRouter(
    prefix="/panels",
    tags=["panels"],
)


@router.post(
    "/",
    response_model=PanelResponse,
    status_code=201,
)
def create_panel(panel: PanelCreate):

    created_panel = add_panel(
        lon=panel.longitude,
        lat=panel.latitude,
        address=panel.address,
        address_complement=panel.address_complement,
        surface_m2=panel.surface_m2,
    )

    return panel_to_response(created_panel)


@router.get(
    "/",
    response_model=PanelFeatureCollection,
)
def read_panels(
    min_lon: float = Query(ge=-180, le=180),
    min_lat: float = Query(ge=-90, le=90),
    max_lon: float = Query(ge=-180, le=180),
    max_lat: float = Query(ge=-90, le=90),
):
    panels = get_panels_in_bbox(
        min_lon=min_lon,
        min_lat=min_lat,
        max_lon=max_lon,
        max_lat=max_lat,
    )

    return panels_to_feature_collection(panels)


@router.get(
    "/{panel_id}",
    response_model=PanelResponse,
)
def read_panel(panel_id: UUID):

    panel = get_panel(str(panel_id))

    if panel is None:
        raise HTTPException(
            status_code=404,
            detail="Panel not found",
        )

    return panel_to_response(panel)
