from datetime import datetime

from pydantic import BaseModel, Field

from typing import Literal

from app.schemas.panel_event import EventType


class PointGeometry(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: list[float]


class PanelProperties(BaseModel):
    id: str
    address: str | None
    address_complement: str | None
    surface_m2: float | None
    status: str

    latest_event_type: EventType | None = None
    latest_event_created_at: datetime | None = None

    commune_code: str


class PanelFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: PointGeometry
    properties: PanelProperties


class PanelFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[PanelFeature]


class PanelCreate(BaseModel):
    longitude: float = Field(ge=-180, le=180)
    latitude: float = Field(ge=-90, le=90)

    address: str | None = None
    address_complement: str | None = None
    surface_m2: float | None = Field(default=None, gt=0)


class PanelResponse(BaseModel):
    id: str

    address: str | None
    address_complement: str | None

    location: PointGeometry

    surface_m2: float | None
    status: str

    source_id: str | None
    source: str

    commune_code: str
    created_at: datetime
