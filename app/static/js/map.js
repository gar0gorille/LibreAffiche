import * as maplibregl
    from "https://unpkg.com/maplibre-gl@^6.11.2/dist/maplibre-gl.mjs";


const map = new maplibregl.Map({
    container: "map",

    style: "https://tiles.openfreemap.org/styles/liberty",

    center: [3.16, 50.69],

    zoom: 13,
});


map.addControl(
    new maplibregl.NavigationControl(),
    "top-right"
);


async function fetchPanels() {

    const bounds = map.getBounds();

    const params = new URLSearchParams({
        min_lon: bounds.getWest(),
        min_lat: bounds.getSouth(),
        max_lon: bounds.getEast(),
        max_lat: bounds.getNorth(),
    });

    const response = await fetch(
        `/panels/?${params}`
    );

    if (!response.ok) {
        throw new Error(
            `Failed to load panels: ${response.status}`
        );
    }

    return await response.json();
}


map.on("load", async () => {

    const geojson = await fetchPanels();

    map.addSource(
        "panels",
        {
            type: "geojson",
            data: geojson,
        }
    );

    map.addLayer({
        id: "panels-points",

        type: "circle",

        source: "panels",

        paint: {
            "circle-radius": 7,
            "circle-stroke-width": 2,
            "circle-stroke-color": "#ffffff",
        },
    });

});