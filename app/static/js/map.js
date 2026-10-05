import * as maplibregl
    from "https://unpkg.com/maplibre-gl@^6.11.2/dist/maplibre-gl.mjs";


import {
    fetchPanels
} from "./api.js";


import {
    setupAddPanel,
    isAddPanelMode,
} from "./add-panel.js";


import {
    showPanelPopup
} from "./panel-popup.js";



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


// --------------------------------------------------
// Chargement / refresh panneaux
// --------------------------------------------------

async function refreshPanels() {

    const bounds =
        map.getBounds();


    const geojson =
        await fetchPanels(

            bounds.getWest(),
            bounds.getSouth(),
            bounds.getEast(),
            bounds.getNorth()

        );


    const source =
        map.getSource("panels");


    if (source) {
        source.setData(geojson);
    }


    return geojson;
}


// --------------------------------------------------
// Initialisation carte
// --------------------------------------------------

map.on("load", async () => {

    const geojson =
        await refreshPanels();


    map.addSource("panels", {
        type: "geojson",
        data: geojson,
    });


    map.addLayer({

        id: "panels-points",

        type: "circle",

        source: "panels",

        paint: {

            "circle-radius": 7,

            "circle-color": [
                "match",
                ["get", "status"],

                "POSTER_ADDED", "#2a9d8f",
                "VISIBLE", "#2a9d8f",
                "PARTIALLY_COVERED", "#f4a261",
                "COVERED", "#e63946",
                "EMPTY", "#6c757d",
                "POSTER_REMOVED", "#151718",

                "#457b9d"
            ],

            "circle-stroke-width": 2,

            "circle-stroke-color":
                "#ffffff",
        },
    });


    // -----------------------------
    // Interaction panneaux
    // -----------------------------

    map.on(
        "click",
        "panels-points",
        (e) => {

            if (isAddPanelMode()) {
                return;
            }

            showPanelPopup(
                map,
                maplibregl,
                e.features[0]
            );
        }
    );


    map.on(
        "mouseenter",
        "panels-points",
        () => {

            if (!isAddPanelMode()) {

                map.getCanvas()
                    .style.cursor =
                    "pointer";
            }
        }
    );


    map.on(
        "mouseleave",
        "panels-points",
        () => {

            if (!isAddPanelMode()) {

                map.getCanvas()
                    .style.cursor =
                    "";
            }
        }
    );

});


// --------------------------------------------------
// Déplacement carte
// --------------------------------------------------

map.on("moveend", async () => {

    try {

        if (!map.getSource("panels")) {
            return;
        }

        await refreshPanels();

    } catch (error) {

        console.error(
            "Erreur chargement panneaux :",
            error
        );
    }

});


// --------------------------------------------------
// Module ajout panneau
// --------------------------------------------------

setupAddPanel(
    map,
    maplibregl,
    refreshPanels
);