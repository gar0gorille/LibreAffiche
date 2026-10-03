from app.mappers.panel import panel_to_feature


def test_panel_to_feature_contains_latest_event(fake_panel):

    feature = panel_to_feature(fake_panel)

    assert feature["type"] == "Feature"

    assert feature["geometry"] == {
        "type": "Point",
        "coordinates": [
            2.428689,
            48.728042,
        ],
    }

    properties = feature["properties"]

    assert properties["id"] == fake_panel["id"]
    assert properties["status"] == "AVAILABLE"

    assert properties["latest_event_type"] == "COVERED"
    assert (
        properties["latest_event_created_at"] == fake_panel["latest_event_created_at"]
    )


def test_panel_to_feature_without_event(
    fake_panel_without_event,
):

    feature = panel_to_feature(fake_panel_without_event)

    properties = feature["properties"]

    assert properties["latest_event_type"] is None
    assert properties["latest_event_created_at"] is None
