def test_get_panel(client, monkeypatch, fake_panel):

    monkeypatch.setattr(
        "app.api.panel.get_panel",
        lambda panel_id: fake_panel,
    )

    response = client.get(f"/panels/{fake_panel['id']}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == fake_panel["id"]

    assert data["location"] == {
        "type": "Point",
        "coordinates": [
            2.428689,
            48.728042,
        ],
    }


def test_get_panel_invalid_uuid(client):

    response = client.get("/panels/not-a-valid-uuid")

    assert response.status_code == 422


def test_get_unknown_panel_returns_404(
    client,
    monkeypatch,
):
    unknown_id = "11111111-1111-1111-1111-111111111111"

    monkeypatch.setattr(
        "app.api.panel.get_panel",
        lambda panel_id: None,
    )

    response = client.get(f"/panels/{unknown_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Panel not found"


def test_create_panel(
    client,
    monkeypatch,
    fake_panel,
):
    def fake_add_panel(
        lon,
        lat,
        address=None,
        address_complement=None,
        surface_m2=None,
        source="user",
        source_id=None,
    ):
        return {
            **fake_panel,
            "longitude": lon,
            "latitude": lat,
            "address": address,
            "address_complement": address_complement,
            "surface_m2": surface_m2,
        }

    monkeypatch.setattr(
        "app.api.panel.add_panel",
        fake_add_panel,
    )

    response = client.post(
        "/panels/",
        json={
            "longitude": 2.428689,
            "latitude": 48.728042,
            "address": "2 Rue Pierre Loti",
            "surface_m2": 2.0,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == fake_panel["id"]
    assert data["address"] == "2 Rue Pierre Loti"
    assert data["location"]["coordinates"] == [
        2.428689,
        48.728042,
    ]


def test_create_panel_invalid_longitude(client):

    response = client.post(
        "/panels/",
        json={
            "longitude": 250,
            "latitude": 48.7,
        },
    )

    assert response.status_code == 422


def test_create_panel_invalid_latitude(client):

    response = client.post(
        "/panels/",
        json={
            "longitude": 2.4,
            "latitude": -150,
        },
    )

    assert response.status_code == 422


def test_create_panel_negative_surface(client):

    response = client.post(
        "/panels/",
        json={
            "longitude": 2.4,
            "latitude": 48.7,
            "surface_m2": -2,
        },
    )

    assert response.status_code == 422


def test_create_panel_missing_coordinates(client):

    response = client.post(
        "/panels/",
        json={
            "address": "Quelque part",
        },
    )

    assert response.status_code == 422


def test_get_panels_in_bbox(
    client,
    monkeypatch,
    fake_panel,
):

    monkeypatch.setattr(
        "app.api.panel.get_panels_in_bbox",
        lambda **kwargs: [fake_panel],
    )

    response = client.get(
        "/panels/",
        params={
            "min_lon": 2.0,
            "min_lat": 48.0,
            "max_lon": 3.0,
            "max_lat": 49.0,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 1

    feature = data["features"][0]

    assert feature["type"] == "Feature"

    assert feature["geometry"] == {
        "type": "Point",
        "coordinates": [
            2.428689,
            48.728042,
        ],
    }

    assert feature["properties"]["id"] == fake_panel["id"]
    assert feature["properties"]["status"] == "AVAILABLE"


def test_bbox_invalid_longitude(client):

    response = client.get(
        "/panels/",
        params={
            "min_lon": -500,
            "min_lat": 48,
            "max_lon": 3,
            "max_lat": 49,
        },
    )

    assert response.status_code == 422


def test_bbox_returns_latest_event(
    client,
    monkeypatch,
    fake_panel,
):

    monkeypatch.setattr(
        "app.api.panel.get_panels_in_bbox",
        lambda **kwargs: [fake_panel],
    )

    response = client.get(
        "/panels/",
        params={
            "min_lon": 2.0,
            "min_lat": 48.0,
            "max_lon": 3.0,
            "max_lat": 49.0,
        },
    )

    assert response.status_code == 200

    data = response.json()

    feature = data["features"][0]
    assert feature["properties"]["latest_event_type"] == "COVERED"

    assert feature["properties"]["latest_event_created_at"] is not None


def test_bbox_panel_without_event(
    client,
    monkeypatch,
    fake_panel_without_event,
):

    monkeypatch.setattr(
        "app.api.panel.get_panels_in_bbox",
        lambda **kwargs: [fake_panel_without_event],
    )

    response = client.get(
        "/panels/",
        params={
            "min_lon": 2.0,
            "min_lat": 48.0,
            "max_lon": 3.0,
            "max_lat": 49.0,
        },
    )

    assert response.status_code == 200

    feature = response.json()["features"][0]

    assert feature["properties"]["latest_event_type"] is None

    assert feature["properties"]["latest_event_created_at"] is None
