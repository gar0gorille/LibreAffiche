from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def fake_panel():
    return {
        "id": "e7abc4fe-02ac-41c2-89bf-a94eaabbcfb5",
        "address": "2 Rue Pierre Loti",
        "address_complement": None,
        "longitude": 2.428689,
        "latitude": 48.728042,
        "surface_m2": 2.0,
        "status": "AVAILABLE",
        "source_id": None,
        "source": "user",
        "commune_code": "94003",
        "created_at": datetime(
            2026,
            10,
            2,
            18,
            0,
            tzinfo=timezone.utc,
        ),
        "latest_event_type": "COVERED",
        "latest_event_created_at": datetime(
            2026,
            10,
            2,
            19,
            30,
            tzinfo=timezone.utc,
        ),
    }


@pytest.fixture
def fake_panel_without_event(fake_panel):
    panel = fake_panel.copy()

    panel["id"] = "11111111-1111-1111-1111-111111111111"
    panel["latest_event_type"] = None
    panel["latest_event_created_at"] = None

    return panel
