"""Tests des routes FastAPI (sans accès à PostgreSQL).

Ces tests supposent que les routers sont dans app.api. Si ton projet utilise
app.routers, adapte les trois imports de routers ci-dessous.
"""

from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import commune as commune_api
from app.api import panel as panel_api
from app.api import panel_event as event_api


PANEL_ID = "example-panel-42"  # Teste aussi les identifiants non UUID.
CREATED_AT = datetime(2026, 10, 10, 10, 0, tzinfo=timezone.utc)


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(commune_api.router)
    app.include_router(panel_api.router)
    app.include_router(event_api.router)
    with TestClient(app) as http_client:
        yield http_client


def panel_row(**overrides):
    """Dictionnaire brut tel que le repository l'envoie au mapper."""
    row = {
        "id": PANEL_ID,
        "longitude": 3.16,
        "latitude": 50.69,
        "address": "2 rue de test",
        "address_complement": None,
        "surface_m2": 2.5,
        "status": "AVAILABLE",
        "source_id": None,
        "source": "user",
        "commune_code": "59512",
        "created_at": CREATED_AT,
        "latest_event_type": "COVERED",
        "latest_event_created_at": CREATED_AT,
    }
    row.update(overrides)
    return row


def event_row(**overrides):
    row = {
        "event_id": "e-1",
        "panel_id": PANEL_ID,
        "created_at": CREATED_AT,
        "event_type": "COVERED",
        "comment": "Affiche recouverte",
        "source_id": None,
        "source": "user",
    }
    row.update(overrides)
    return row


def test_commune_found(client, monkeypatch):
    monkeypatch.setattr(
        commune_api, "get_commune", lambda lon, lat: {"code": "59512", "nom": "Roubaix"}
    )
    response = client.get("/communes/?lon=3.16&lat=50.69")
    assert response.status_code == 200
    assert response.json() == {"commune_code": "59512", "commune_name": "Roubaix"}


def test_commune_not_found(client, monkeypatch):
    monkeypatch.setattr(commune_api, "get_commune", lambda lon, lat: None)
    assert client.get("/communes/?lon=3.16&lat=50.69").status_code == 404


@pytest.mark.parametrize("params", ["lon=190&lat=40", "lon=NaN&lat=40", "lon=3.16"])
def test_commune_invalid_coordinates(client, params):
    assert client.get(f"/communes/?{params}").status_code == 422


def test_create_panel_success(client, monkeypatch):
    monkeypatch.setattr(panel_api, "add_panel", lambda **kwargs: panel_row())
    response = client.post(
        "/panels/",
        json={"longitude": 3.16, "latitude": 50.69, "surface_m2": 2.5},
    )
    assert response.status_code == 201
    assert response.json()["location"]["coordinates"] == [3.16, 50.69]
    assert response.json()["id"] == PANEL_ID


def test_create_panel_duplicate_returns_409(client, monkeypatch):
    def duplicate(**kwargs):
        raise ValueError("Panel already exists nearby (id=123, distance=1.0 m)")
    monkeypatch.setattr(panel_api, "add_panel", duplicate)
    response = client.post("/panels/", json={"longitude": 3.16, "latitude": 50.69})
    assert response.status_code == 409
    assert "already exists nearby" in response.json()["detail"]


def test_create_panel_no_commune_returns_422(client, monkeypatch):
    def outside(**kwargs):
        raise ValueError("No commune found for coordinates (3.16, 50.69)")
    monkeypatch.setattr(panel_api, "add_panel", outside)
    assert client.post(
        "/panels/", json={"longitude": 3.16, "latitude": 50.69}
    ).status_code == 422


@pytest.mark.parametrize("surface", [-1, 0, "NaN"])
def test_create_panel_invalid_surface_returns_422(client, surface):
    response = client.post(
        "/panels/",
        json={"longitude": 3.16, "latitude": 50.69, "surface_m2": surface},
    )
    assert response.status_code == 422


def test_read_panels_geojson_includes_latest_event(client, monkeypatch):
    monkeypatch.setattr(panel_api, "get_panels_in_bbox", lambda **kwargs: [panel_row()])
    response = client.get("/panels/?min_lon=3&min_lat=50&max_lon=4&max_lat=51")
    assert response.status_code == 200
    assert response.json()["type"] == "FeatureCollection"
    feature = response.json()["features"][0]
    assert feature["geometry"]["coordinates"] == [3.16, 50.69]
    assert feature["properties"]["latest_event_type"] == "COVERED"
    assert feature["properties"]["latest_event_created_at"] is not None


def test_read_panels_without_events(client, monkeypatch):
    monkeypatch.setattr(
        panel_api,
        "get_panels_in_bbox",
        lambda **kwargs: [panel_row(latest_event_type=None, latest_event_created_at=None)],
    )
    response = client.get("/panels/?min_lon=3&min_lat=50&max_lon=4&max_lat=51")
    assert response.status_code == 200
    assert response.json()["features"][0]["properties"]["latest_event_type"] is None


def test_read_panels_empty_returns_empty_geojson(client, monkeypatch):
    monkeypatch.setattr(panel_api, "get_panels_in_bbox", lambda **kwargs: [])
    response = client.get("/panels/?min_lon=3&min_lat=50&max_lon=4&max_lat=51")
    assert response.status_code == 200
    assert response.json() == {"type": "FeatureCollection", "features": []}


@pytest.mark.parametrize(
    "bbox", ["min_lon=4&min_lat=50&max_lon=3&max_lat=51", "min_lon=3&min_lat=51&max_lon=4&max_lat=50"]
)
def test_read_panels_rejects_reversed_bbox(client, bbox):
    assert client.get(f"/panels/?{bbox}").status_code == 422


def test_read_panel_non_uuid_id(client, monkeypatch):
    monkeypatch.setattr(panel_api, "get_panel", lambda panel_id: panel_row())
    response = client.get(f"/panels/{PANEL_ID}")
    assert response.status_code == 200
    assert response.json()["id"] == PANEL_ID


def test_read_panel_unknown_returns_404(client, monkeypatch):
    monkeypatch.setattr(panel_api, "get_panel", lambda panel_id: None)
    assert client.get(f"/panels/{PANEL_ID}").status_code == 404


def test_post_panel_event_success(client, monkeypatch):
    monkeypatch.setattr(event_api, "get_panel", lambda panel_id: panel_row())
    monkeypatch.setattr(event_api, "add_panel_event", lambda **kwargs: event_row())
    response = client.post(
        f"/panels/{PANEL_ID}/events/",
        json={"event_type": "COVERED", "comment": "Affiche recouverte"},
    )
    assert response.status_code == 201
    assert response.json()["event_type"] == "COVERED"


def test_post_panel_event_unknown_panel_returns_404(client, monkeypatch):
    monkeypatch.setattr(event_api, "get_panel", lambda panel_id: None)
    assert client.post(
        f"/panels/{PANEL_ID}/events/", json={"event_type": "VISIBLE"}
    ).status_code == 404


def test_post_panel_event_invalid_type_returns_422(client):
    response = client.post(
        f"/panels/{PANEL_ID}/events/", json={"event_type": "BOGUS"},
    )
    assert response.status_code == 422


def test_panel_history_existing_panel_no_events_returns_list(client, monkeypatch):
    monkeypatch.setattr(event_api, "get_panel", lambda panel_id: panel_row())
    monkeypatch.setattr(event_api, "get_panel_history", lambda panel_id: [])
    response = client.get(f"/panels/{PANEL_ID}/events/")
    assert response.status_code == 200
    assert response.json() == []


def test_panel_history_existing_panel_with_events(client, monkeypatch):
    monkeypatch.setattr(event_api, "get_panel", lambda panel_id: panel_row())
    monkeypatch.setattr(event_api, "get_panel_history", lambda panel_id: [event_row()])
    response = client.get(f"/panels/{PANEL_ID}/events/")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["event_type"] == "COVERED"


def test_panel_history_unknown_panel_returns_404(client, monkeypatch):
    monkeypatch.setattr(event_api, "get_panel", lambda panel_id: None)
    assert client.get(f"/panels/{PANEL_ID}/events/").status_code == 404
