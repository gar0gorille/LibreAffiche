import pytest
from pydantic import ValidationError

from app.schemas.panel import PanelCreate
from app.schemas.panel_event import PanelEventCreate


def test_panel_create_valid():
    panel = PanelCreate(
        longitude=2.4,
        latitude=48.7,
        surface_m2=2,
    )

    assert panel.longitude == 2.4
    assert panel.latitude == 48.7
    assert panel.surface_m2 == 2


def test_panel_invalid_longitude():
    with pytest.raises(ValidationError):
        PanelCreate(
            longitude=300,
            latitude=48,
        )


def test_panel_invalid_latitude():
    with pytest.raises(ValidationError):
        PanelCreate(
            longitude=2,
            latitude=100,
        )


def test_panel_negative_surface():
    with pytest.raises(ValidationError):
        PanelCreate(
            longitude=2,
            latitude=48,
            surface_m2=-1,
        )


@pytest.mark.parametrize(
    "event_type",
    [
        "POSTER_ADDED",
        "VISIBLE",
        "COVERED",
        "PARTIALLY_COVERED",
        "EMPTY",
        "POSTER_REMOVED",
    ],
)
def test_valid_event_types(event_type):
    event = PanelEventCreate(
        event_type=event_type,
    )

    assert event.event_type == event_type


def test_invalid_event_type():
    with pytest.raises(ValidationError):
        PanelEventCreate(
            event_type="BANANA",
        )
