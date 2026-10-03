from sqlalchemy import text

from app.database import engine

from uuid import uuid4

from app.repositories.commune import get_commune


DUPLICATE_DISTANCE_M = 5


def find_nearby_panel(
    lon: float,
    lat: float,
    distance_m: float = DUPLICATE_DISTANCE_M,
):
    """
    Return the closest existing panel within `distance_m`,
    or None if no panel is found.
    """

    query = text("""
        SELECT
            id,
            address,
            ST_Distance(
                location::geography,
                ST_SetSRID(
                    ST_Point(:lon, :lat),
                    4326
                )::geography
            ) AS distance_m
        FROM panels
        WHERE ST_DWithin(
            location::geography,
            ST_SetSRID(
                ST_Point(:lon, :lat),
                4326
            )::geography,
            :distance_m
        )
        ORDER BY distance_m
        LIMIT 1
    """)

    with engine.connect() as conn:
        return conn.execute(
            query,
            {
                "lon": lon,
                "lat": lat,
                "distance_m": distance_m,
            },
        ).first()


def add_panel(
    lon: float,
    lat: float,
    address: str | None = None,
    address_complement: str | None = None,
    surface_m2: float | None = None,
    source: str = "user",
    source_id: str | None = None,
):
    """
    Add a panel to the database.

    Minimum required information:
        - longitude
        - latitude

    The commune is automatically determined from the coordinates.
    """

    # Basic coordinate validation
    if not -180 <= lon <= 180:
        raise ValueError(f"Invalid longitude: {lon}")

    if not -90 <= lat <= 90:
        raise ValueError(f"Invalid latitude: {lat}")

    # Prevent likely duplicate panels
    existing_panel = find_nearby_panel(lon, lat)

    if existing_panel is not None:
        raise ValueError(
            f"Panel already exists nearby "
            f"(id={existing_panel.id}, "
            f"distance={existing_panel.distance_m:.1f} m)"
        )

    # Determine the commune from the coordinates
    commune = get_commune(lon, lat)

    if commune is None:
        raise ValueError(f"No commune found for coordinates ({lon}, {lat})")

    panel_id = str(uuid4())

    query = text("""
        INSERT INTO panels (
            id,
            address,
            address_complement,
            location,
            surface_m2,
            status,
            source_id,
            source,
            commune_code
        )
        VALUES (
            :id,
            :address,
            :address_complement,
            ST_SetSRID(
                ST_Point(:lon, :lat),
                4326
            ),
            :surface_m2,
            'AVAILABLE',
            :source_id,
            :source,
            :commune_code
        )
        RETURNING id, created_at
    """)

    # begin() automatically commits if everything succeeds,
    # and rolls back if an exception occurs.
    with engine.begin() as conn:
        row = (
            conn.execute(
                query,
                {
                    "id": panel_id,
                    "lon": lon,
                    "lat": lat,
                    "address": address,
                    "address_complement": address_complement,
                    "surface_m2": surface_m2,
                    "source_id": source_id,
                    "source": source,
                    "commune_code": commune["code"],
                },
            )
            .mappings()
            .one()
        )

    return {
        "id": panel_id,
        "longitude": lon,
        "latitude": lat,
        "address": address,
        "address_complement": address_complement,
        "surface_m2": surface_m2,
        "status": "AVAILABLE",
        "source_id": source_id,
        "source": source,
        "created_at": row["created_at"],
        "commune_code": commune["code"],
        "commune_name": commune["nom"],
    }


def get_panel(panel_id: str):
    """
    Return one panel from its ID.
    """

    query = text("""
        SELECT
            id,
            address,
            address_complement,
            ST_X(location) AS longitude,
            ST_Y(location) AS latitude,
            surface_m2,
            status,
            source_id,
            source,
            commune_code,
            created_at
        FROM panels
        WHERE id = :panel_id
        """)

    with engine.connect() as conn:
        row = (
            conn.execute(
                query,
                {"panel_id": panel_id},
            )
            .mappings()
            .first()
        )

    if row is None:
        return None

    return dict(row)


def get_panels_in_bbox(
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
):
    query = text("""
        SELECT
            p.id,
            p.address,
            p.address_complement,
            ST_X(p.location) AS longitude,
            ST_Y(p.location) AS latitude,
            p.surface_m2,
            p.status,
            p.source_id,
            p.source,
            p.commune_code,
            p.created_at,

            latest_event.event_type AS latest_event_type,
            latest_event.created_at AS latest_event_created_at

        FROM panels AS p

        LEFT JOIN LATERAL (
            SELECT
                pe.event_type,
                pe.created_at
            FROM panel_events AS pe
            WHERE pe.panel_id = p.id
            ORDER BY pe.created_at DESC
            LIMIT 1
        ) AS latest_event ON TRUE

        WHERE ST_Intersects(
            p.location,
            ST_MakeEnvelope(
                :min_lon,
                :min_lat,
                :max_lon,
                :max_lat,
                4326
            )
        )
    """)

    with engine.connect() as conn:
        rows = (
            conn.execute(
                query,
                {
                    "min_lon": min_lon,
                    "min_lat": min_lat,
                    "max_lon": max_lon,
                    "max_lat": max_lat,
                },
            )
            .mappings()
            .all()
        )

    return [dict(row) for row in rows]
