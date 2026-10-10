"""Routes HTTP des signalements (événements) associés à un panneau.

Un événement est une observation horodatée : COVERED, VISIBLE, EMPTY, etc.
L'historique ne modifie pas ``panels.status``. Le dernier événement est
rechargé par le repository des panneaux pour déterminer la couleur MapLibre.
"""

from fastapi import APIRouter, HTTPException, Path, status

from app.repositories.panel import get_panel
from app.repositories.panel_event import add_panel_event, get_panel_history
from app.schemas.panel_event import PanelEventCreate, PanelEventResponse


router = APIRouter(prefix="/panels/{panel_id}/events", tags=["events"])


def _ensure_panel_exists(panel_id: str) -> None:
    """Vérifie l'existence du panneau pour les routes POST et GET.

    Sans contrôle, un POST vers un ID inconnu échouerait potentiellement sur
    la clé étrangère SQL et renverrait un code 500 au lieu d'un code 404.
    Un panneau existant sans événement doit en revanche avoir un historique [].

    Note : cela ajoute une lecture SQL avant le POST/GET. À grande échelle,
    on pourra créer un ``panel_exists`` léger dans le repository.
    """
    if get_panel(panel_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Panel not found",
        )


@router.post(
    "/",
    response_model=PanelEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Signaler un nouvel événement sur un panneau",
)
def create_panel_event(
    panel_event: PanelEventCreate,
    panel_id: str = Path(description="Identifiant du panneau concerné"),
):
    """Crée un signalement sur un panneau existant.

    Le corps est validé par Pydantic : seuls les six ``EventType`` autorisés
    sont acceptés (sinon HTTP 422). L'horodatage est fourni par PostgreSQL.
    """
    _ensure_panel_exists(panel_id)

    return add_panel_event(
        panel_id=panel_id,
        event_type=panel_event.event_type,
        comment=panel_event.comment,
    )


@router.get(
    "/",
    response_model=list[PanelEventResponse],
    summary="Lire l'historique des événements d'un panneau",
)
def read_panel_event_history(
    panel_id: str = Path(description="Identifiant du panneau concerné"),
):
    """Liste les événements du plus ancien au plus récent.

    - panneau inexistant : 404 ;
    - panneau existant sans signalement : 200 avec liste vide [] ;
    - panneau avec signalements : 200 avec les événements ordonnés.
    """
    _ensure_panel_exists(panel_id)
    return get_panel_history(panel_id)
