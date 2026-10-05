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
    PANEL_COLOR_EXPRESSION,
    PANEL_STATUSES,
} from "./panel-status.js";

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
// Module : circles colour's legend
// --------------------------------------------------

function addMapLegend() {

    const legendStatuses = [
        PANEL_STATUSES.VISIBLE,
        PANEL_STATUSES.PARTIALLY_COVERED,
        PANEL_STATUSES.COVERED,
        PANEL_STATUSES.EMPTY,
        PANEL_STATUSES.POSTER_REMOVED,
    ];


    const legendControl = {

        onAdd() {

            const container =
                document.createElement("div");

            container.className =
                "maplibregl-ctrl";


            container.style.cssText = `
                font-family: Arial, sans-serif;
                font-size: 12px;
            `;


            const button =
                document.createElement("button");

            button.type = "button";

            button.textContent = "Légende";

            button.style.cssText = `
                background: white;
                border: none;
                border-radius: 8px;
                padding: 8px 12px;

                cursor: pointer;

                box-shadow:
                    0 1px 5px rgba(0, 0, 0, 0.25);

                font-size: 12px;
                font-weight: 600;
            `;


            const panel =
                document.createElement("div");

            panel.style.cssText = `
                display: none;

                margin-top: 6px;

                width: 175px;

                padding: 10px;

                background: white;

                border-radius: 8px;

                box-shadow:
                    0 1px 5px rgba(0, 0, 0, 0.25);
            `;


            panel.innerHTML = `
                ${legendStatuses
                    .map(status => `
                        <div style="
                            display: flex;
                            align-items: center;
                            gap: 8px;
                            margin: 6px 0;
                        ">

                            <span style="
                                display: inline-block;

                                width: 10px;
                                height: 10px;

                                min-width: 10px;

                                border-radius: 50%;

                                background-color:
                                    ${status.color};
                            ">
                            </span>

                            <span>
                                ${status.label}
                            </span>

                        </div>
                    `)
                    .join("")
                }
            `;


            button.addEventListener(
                "click",
                () => {

                    const isOpen =
                        panel.style.display !== "none";


                    panel.style.display =
                        isOpen
                            ? "none"
                            : "block";


                    button.textContent =
                        isOpen
                            ? "Légende"
                            : "Fermer";
                }
            );


            container.appendChild(button);
            container.appendChild(panel);


            this.container = container;

            return container;
        },


        onRemove() {

            this.container.remove();

            this.container = null;
        }
    };


    map.addControl(
        legendControl,
        "top-left"
    );
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

            "circle-color":
                PANEL_COLOR_EXPRESSION,

            "circle-stroke-width": 2,

            "circle-stroke-color":
                "#ffffff",
        },
    });


    addMapLegend();


    // --------------------------------
    // Interactions panneaux
    // --------------------------------

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
                    .style.cursor = "";
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

