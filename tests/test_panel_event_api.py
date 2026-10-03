from datetime import datetime, timezone


PANEL_ID = "e7abc4fe-02ac-41c2-89bf-a94eaabbcfb5"
EVENT_ID = "e2da61be-cd79-45c0-a776-fbd66fb2911c"


FAKE_EVENT = {
    "event_id": EVENT_ID,
    "panel_id": PANEL_ID,
    "created_at": datetime(
        2026,
        10,
        2,
        19,
        0,
        tzinfo=timezone.utc,
    ),
    "event_type": "COVERED",
    "comment": "Affiche recouverte",
    "source_id": None,
    "source": "user",
}


def test_create_panel_event(
    client,
    monkeypatch,
):
    def fake_add_panel_event(
        panel_id,
        event_type,
        comment=None,
        source="user",
        source_id=None,
    ):
        assert panel_id == PANEL_ID
        assert event_type == "COVERED"

        return FAKE_EVENT

    monkeypatch.setattr(
        "app.api.panel_event.add_panel_event",
        fake_add_panel_event,
    )

    response = client.post(
        f"/panels/{PANEL_ID}/events/",
        json={
            "event_type": "COVERED",
            "comment": "Affiche recouverte",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["panel_id"] == PANEL_ID
    assert data["event_type"] == "COVERED"
    assert data["comment"] == "Affiche recouverte"


def test_create_event_without_comment(
    client,
    monkeypatch,
):
    def fake_add_panel_event(
        panel_id,
        event_type,
        comment=None,
        **kwargs,
    ):
        return {
            **FAKE_EVENT,
            "event_type": event_type,
            "comment": comment,
        }

    monkeypatch.setattr(
        "app.api.panel_event.add_panel_event",
        fake_add_panel_event,
    )

    response = client.post(
        f"/panels/{PANEL_ID}/events/",
        json={
            "event_type": "VISIBLE",
        },
    )

    assert response.status_code == 201
    assert response.json()["event_type"] == "VISIBLE"
    assert response.json()["comment"] is None


def test_invalid_event_type(client):
    response = client.post(
        f"/panels/{PANEL_ID}/events/",
        json={
            "event_type": "BANANA",
        },
    )

    assert response.status_code == 422


def test_get_panel_history(
    client,
    monkeypatch,
):
    fake_history = [
        {
            **FAKE_EVENT,
            "event_type": "POSTER_ADDED",
            "comment": None,
        },
        FAKE_EVENT,
    ]

    monkeypatch.setattr(
        "app.api.panel_event.get_panel_history",
        lambda panel_id: fake_history,
    )

    response = client.get(f"/panels/{PANEL_ID}/events/")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["event_type"] == "POSTER_ADDED"
    assert data[1]["event_type"] == "COVERED"
