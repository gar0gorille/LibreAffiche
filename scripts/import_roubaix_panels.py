import geopandas as gpd
from shapely import force_2d
from uuid import uuid4

from app.database import engine


gdf = gpd.read_file("data/panneaux_roubaix.geojson")

rename_col = {
    "adresse": "address",
    "complement_adresse": "address_complement",
    "geometry": "location",
}

gdf = gdf.rename(columns=rename_col)
gdf = gdf.set_geometry("location")

# LibreAffiche fields
gdf["id"] = [str(uuid4()) for _ in range(len(gdf))]
gdf["status"] = "UNKNOWN"

gdf["source"] = "roubaix_open_data"
gdf["source_id"] = gdf["id_panneau"]
gdf["commune_code"] = "59512"

# Remove useless Z coordinate
gdf["location"] = gdf.location.apply(force_2d)

gdf = gdf[
    [
        "id",
        "address",
        "address_complement",
        "location",
        "surface_m2",
        "status",
        "source_id",
        "source",
        "commune_code",
    ]
]

CHUNK_SIZE = 500

for i in range(0, len(gdf), CHUNK_SIZE):
    chunk = gdf.iloc[i : i + CHUNK_SIZE]

    chunk.to_postgis(
        name="panels",
        con=engine,
        if_exists="append",
        index=False,
    )

    print(f"{min(i + CHUNK_SIZE, len(gdf))}/{len(gdf)} panneaux importés")
