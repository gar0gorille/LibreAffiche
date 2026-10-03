from fastapi import APIRouter

from app.repositories.panel_event import (
    add_panel_event,
    get_panel_history,
)
from app.schemas.panel_event import (
    PanelEventCreate,
    PanelEventResponse,
)


router = APIRouter(
    prefix="/panels/{panel_id}/events",
    tags=["events"],
)


@router.post(
    "/",
    response_model=PanelEventResponse,
    status_code=201,
)
def create_panel_event(
    panel_id: str,
    panel_event: PanelEventCreate,
):
    return add_panel_event(
        panel_id=panel_id,
        event_type=panel_event.event_type,
        comment=panel_event.comment,
    )


@router.get(
    "/",
    response_model=list[PanelEventResponse],
)
def read_panel_event_history(
    panel_id: str,
):
    return get_panel_history(panel_id)
