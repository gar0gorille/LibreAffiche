import geopandas as gpd
from shapely.geometry import MultiPolygon

from app.database import engine


gdf = gpd.read_file("data/communes_france_20250417.geojson")

# On garde uniquement ce qui nous intéresse
gdf = gdf[
    [
        "code",
        "nom",
        "departement",
        "region",
        "epci",
        "geometry",
    ]
].copy()

# Tous les Polygon deviennent des MultiPolygon
gdf["geometry"] = gdf["geometry"].apply(
    lambda geom: MultiPolygon([geom]) if geom.geom_type == "Polygon" else geom
)

print(gdf.geometry.geom_type.value_counts())

CHUNK_SIZE = 500

for i in range(0, len(gdf), CHUNK_SIZE):
    chunk = gdf.iloc[i : i + CHUNK_SIZE]

    chunk.to_postgis(
        name="communes",
        con=engine,
        if_exists="append",
        index=False,
    )

    print(f"{min(i + CHUNK_SIZE, len(gdf))}/{len(gdf)} communes importées")
