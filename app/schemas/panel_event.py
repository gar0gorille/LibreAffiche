from datetime import datetime
from typing import Literal

from pydantic import BaseModel


EventType = Literal[
    "POSTER_ADDED",
    "VISIBLE",
    "COVERED",
    "PARTIALLY_COVERED",
    "EMPTY",
    "POSTER_REMOVED",
]


class PanelEventCreate(BaseModel):
    event_type: EventType
    comment: str | None = None


class PanelEventResponse(BaseModel):
    event_id: str
    panel_id: str
    created_at: datetime
    event_type: EventType
    comment: str | None
    source_id: str | None
    source: str
