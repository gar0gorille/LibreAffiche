from sqlalchemy import text

from app.database import engine


def get_commune(lon: float, lat: float):
    """
    Return the smallest commune containing the given coordinates.

    Taking the smallest polygon handles special cases such as Paris,
    where a point can belong both to Paris and to a specific arrondissement.
    """

    query = text("""
        SELECT code, nom
        FROM communes
        WHERE ST_Contains(
            geometry,
            ST_SetSRID(
                ST_Point(:lon, :lat),
                4326
            )
        )
        ORDER BY ST_Area(geometry::geography) ASC
        LIMIT 1
    """)

    with engine.connect() as conn:
        row = (
            conn.execute(
                query,
                {
                    "lon": lon,
                    "lat": lat,
                },
            )
            .mappings()
            .first()
        )

    return row
