"""Tests unitaires du mapper sans connexion à PostgreSQL.

À lancer depuis la racine du projet : pytest -q tests/test_mapper.py
"""

from datetime import datetime, timezone

import pytest

from app.mappers.panel import (
    panel_to_feature,
    panel_to_response,
    panels_to_feature_collection,
)
from app.schemas.panel import PanelFeatureCollection, PanelResponse


@pytest.fixture
def panel():
    return {
        "id": "3b5d7ecc-d69b-4055-9bff-78772b897298",
        "longitude": 3.165,
        "latitude": 50.69,
        "address": "2 Rue Charles Gounod",
        "address_complement": None,
        "surface_m2": 2.5,
        "status": "AVAILABLE",
        "source_id": None,
        "source": "user",
        "commune_code": "59512",
        "created_at": datetime(2026, 10, 10, tzinfo=timezone.utc),
    }


def test_panel_to_response_matches_schema(panel):
    response = panel_to_response(panel)
    validated = PanelResponse.model_validate(response)
    assert validated.location.coordinates == [3.165, 50.69]
    assert validated.status == "AVAILABLE"


def test_new_panel_without_event_is_valid_geojson(panel):
    feature = panel_to_feature(panel)
    validated = PanelFeatureCollection.model_validate(
        {"type": "FeatureCollection", "features": [feature]}
    )
    assert validated.features[0].properties.latest_event_type is None
    assert validated.features[0].properties.latest_event_created_at is None


def test_last_event_is_exposed_for_map_color(panel):
    panel["latest_event_type"] = "COVERED"
    panel["latest_event_created_at"] = datetime(2026, 10, 10, tzinfo=timezone.utc)
    feature = panel_to_feature(panel)
    assert feature["properties"]["latest_event_type"] == "COVERED"
    assert feature["properties"]["status"] == "AVAILABLE"
    assert feature["geometry"]["coordinates"] == [3.165, 50.69]


def test_empty_bbox_produces_valid_feature_collection():
    collection = panels_to_feature_collection([])
    assert PanelFeatureCollection.model_validate(collection).features == []


def test_missing_required_column_is_not_silently_ignored(panel):
    del panel["longitude"]
    with pytest.raises(KeyError, match="longitude"):
        panel_to_feature(panel)


def test_bad_coordinates_are_rejected_by_output_schema(panel):
    panel["latitude"] = 100.0
    with pytest.raises(ValueError):
        PanelFeatureCollection.model_validate(panels_to_feature_collection([panel]))
