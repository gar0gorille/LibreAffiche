import * as maplibregl
    from "https://unpkg.com/maplibre-gl@^6.11.2/dist/maplibre-gl.mjs";


const map = new maplibregl.Map({
    container: "map",
    style: "https://tiles.openfreemap.org/styles/liberty",
    center: [3.16, 50.69],
    zoom: 13,
});


let addPanelMode = false;


map.addControl(
    new maplibregl.NavigationControl(),
    "top-right"
);


const addPanelButton =
    document.getElementById("add-panel-button");


addPanelButton.addEventListener("click", () => {

    addPanelMode = !addPanelMode;

    if (addPanelMode) {

        addPanelButton.textContent = "Annuler";
        map.getCanvas().style.cursor = "crosshair";

    } else {

        addPanelButton.textContent = "+ Ajouter un panneau";
        map.getCanvas().style.cursor = "";
    }
});


// --------------------------------------------------
// API : récupération des panneaux visibles
// --------------------------------------------------

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


// --------------------------------------------------
// Chargement initial de la carte
// --------------------------------------------------

map.on("load", async () => {

    const geojson = await fetchPanels();

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
            "circle-stroke-color": "#ffffff",
        },
    });


    // ----------------------------------------------
    // Clic sur un panneau existant
    // ----------------------------------------------

    map.on("click", "panels-points", (e) => {

        // En mode ajout, on ne veut pas ouvrir
        // la popup du panneau existant
        if (addPanelMode) {
            return;
        }

        const feature = e.features[0];

        const coordinates =
            feature.geometry.coordinates.slice();

        const properties = feature.properties;

        new maplibregl.Popup()
            .setLngLat(coordinates)
            .setHTML(`
                <div class="panel-popup">

                    <strong>
                        ${properties.address ?? "Adresse inconnue"}
                    </strong>

                    <p>
                        Surface :
                        ${properties.surface_m2 ?? "?"} m²
                    </p>

                    <p>
                        État :
                        ${properties.status ?? "UNKNOWN"}
                    </p>

                </div>
            `)
            .addTo(map);
    });


    map.on("mouseenter", "panels-points", () => {

        if (!addPanelMode) {
            map.getCanvas().style.cursor = "pointer";
        }

    });


    map.on("mouseleave", "panels-points", () => {

        if (!addPanelMode) {
            map.getCanvas().style.cursor = "";
        }

    });

});


// --------------------------------------------------
// Rechargement des panneaux après déplacement
// --------------------------------------------------

map.on("moveend", async () => {

    try {

        const source = map.getSource("panels");

        // Sécurité : la source peut ne pas encore exister
        if (!source) {
            return;
        }

        const geojson = await fetchPanels();

        source.setData(geojson);

    } catch (error) {

        console.error(
            "Erreur pendant le chargement des panneaux :",
            error
        );
    }

});


// --------------------------------------------------
// Ajout d'un nouveau panneau
// --------------------------------------------------

map.on("click", (e) => {

    // Clic normal => on ne fait rien
    if (!addPanelMode) {
        return;
    }


    const longitude = e.lngLat.lng;
    const latitude = e.lngLat.lat;


    const popup = new maplibregl.Popup()
        .setLngLat([longitude, latitude])
        .setHTML(`
            <div class="add-panel-popup">

                <strong>
                    Ajouter un panneau
                </strong>

                <form id="add-panel-form">

                    <label for="panel-address">
                        Adresse
                    </label>

                    <input
                        id="panel-address"
                        type="text"
                        required
                    >


                    <label for="panel-address-complement">
                        Précision sur l'emplacement
                    </label>

                    <input
                        id="panel-address-complement"
                        type="text"
                    >


                    <label for="panel-length">
                        Largeur approximative (m)
                    </label>

                    <input
                        id="panel-length"
                        type="number"
                        step="0.1"
                        min="0"
                    >


                    <label for="panel-height">
                        Hauteur approximative (m)
                    </label>

                    <input
                        id="panel-height"
                        type="number"
                        step="0.1"
                        min="0"
                    >


                    <button type="submit">
                        Ajouter
                    </button>

                </form>

            </div>
        `)
        .addTo(map);


    const form =
        document.getElementById("add-panel-form");


    form.addEventListener("submit", async (event) => {

        event.preventDefault();


        const address =
            document.getElementById("panel-address").value;

        const addressComplement =
            document.getElementById(
                "panel-address-complement"
            ).value;

        const length =
            document.getElementById(
                "panel-length"
            ).value;

        const height =
            document.getElementById(
                "panel-height"
            ).value;


        let surface = null;

        if (length && height) {
            surface =
                Number(length) * Number(height);
        }


        try {

            const response = await fetch("/panels/", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                },

                body: JSON.stringify({
                    longitude: longitude,
                    latitude: latitude,
                    address: address,
                    address_complement:
                        addressComplement || null,
                    surface_m2: surface,
                }),

            });


            if (!response.ok) {

                console.error(
                    "Impossible d'ajouter le panneau :",
                    response.status
                );

                return;
            }


            // Ferme le formulaire
            popup.remove();


            // Recharge les panneaux
            const geojson = await fetchPanels();

            const source =
                map.getSource("panels");

            source.setData(geojson);


            // Quitte le mode ajout
            addPanelMode = false;

            addPanelButton.textContent =
                "+ Ajouter un panneau";

            map.getCanvas().style.cursor = "";


        } catch (error) {

            console.error(
                "Erreur lors de l'ajout du panneau :",
                error
            );
        }

    });

});