def panel_to_response(panel: dict) -> dict:
    return {
        "id": panel["id"],
        "address": panel["address"],
        "address_complement": panel["address_complement"],
        "location": {
            "type": "Point",
            "coordinates": [
                panel["longitude"],
                panel["latitude"],
            ],
        },
        "surface_m2": panel["surface_m2"],
        "status": panel["status"],
        "source_id": panel["source_id"],
        "source": panel["source"],
        "commune_code": panel["commune_code"],
        "created_at": panel["created_at"],
    }


def panel_to_feature(panel: dict) -> dict:
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [
                panel["longitude"],
                panel["latitude"],
            ],
        },
        "properties": {
            "id": panel["id"],
            "address": panel["address"],
            "address_complement": panel["address_complement"],
            "surface_m2": panel["surface_m2"],
            "status": panel["status"],
            "latest_event_type": panel["latest_event_type"],
            "latest_event_created_at": panel["latest_event_created_at"],
            "commune_code": panel["commune_code"],
        },
    }


def panels_to_feature_collection(
    panels: list[dict],
) -> dict:
    return {
        "type": "FeatureCollection",
        "features": [panel_to_feature(panel) for panel in panels],
    }
