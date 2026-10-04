def test_get_commune_success(
    client,
    monkeypatch,
):
    def fake_get_commune(lon, lat):
        assert lon == 2.3522
        assert lat == 48.8566

        return {
            "code": "75104",
            "nom": "Paris 4e Arrondissement",
        }

    monkeypatch.setattr(
        "app.api.commune.get_commune",
        fake_get_commune,
    )

    response = client.get(
        "/communes/",
        params={
            "lon": 2.3522,
            "lat": 48.8566,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data == {
        "commune_code": "75104",
        "commune_name": "Paris 4e Arrondissement",
    }


def test_get_commune_not_found(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.commune.get_commune",
        lambda lon, lat: None,
    )

    response = client.get(
        "/communes/",
        params={
            "lon": 0,
            "lat": 0,
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Commune not found"
    }


def test_get_commune_invalid_longitude(client):
    response = client.get(
        "/communes/",
        params={
            "lon": 250,
            "lat": 48,
        },
    )

    assert response.status_code == 422


def test_get_commune_invalid_latitude(client):
    response = client.get(
        "/communes/",
        params={
            "lon": 2,
            "lat": 120,
        },
    )

    assert response.status_code == 422


def test_get_commune_missing_coordinates(client):
    response = client.get(
        "/communes/"
    )

    assert response.status_code == 422