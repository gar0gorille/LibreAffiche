import {
    createPanel,
    fetchCommune,
} from "./api.js";


let addPanelMode = false;

let currentPopup = null;


export function isAddPanelMode() {
    return addPanelMode;
}


function startAddPanelMode(map, button) {

    addPanelMode = true;

    button.textContent = "Annuler";

    map.getCanvas().style.cursor = "crosshair";
}


function stopAddPanelMode(map, button) {

    addPanelMode = false;

    button.textContent = "+ Ajouter un panneau";

    map.getCanvas().style.cursor = "";

    if (currentPopup) {
        currentPopup.remove();
        currentPopup = null;
    }
}


export function setupAddPanel(
    map,
    maplibregl,
    refreshPanels
) {

    const addPanelButton =
        document.getElementById("add-panel-button");


    addPanelButton.addEventListener("click", () => {

        if (addPanelMode) {

            stopAddPanelMode(
                map,
                addPanelButton
            );

        } else {

            startAddPanelMode(
                map,
                addPanelButton
            );
        }
    });


    map.on("click", async (e) => {

        if (!addPanelMode) {
            return;
        }


        const longitude = e.lngLat.lng;
        const latitude = e.lngLat.lat;


        const commune =
            await fetchCommune(
                longitude,
                latitude
            );


        const communeLabel = commune
            ? `${commune.commune_name} (${commune.commune_code})`
            : "Commune non identifiée";


        // Évite d'avoir plusieurs formulaires ouverts
        if (currentPopup) {
            currentPopup.remove();
        }


        currentPopup =
            new maplibregl.Popup({
                maxWidth: "440px",
                closeOnClick: false,
            })
                .setLngLat([
                    longitude,
                    latitude
                ])
                .setHTML(`
                    <div class="add-panel-popup">

                        <h2>
                            Ajouter un panneau
                        </h2>

                        <p>
                            📍 ${communeLabel}
                        </p>

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


                            <p>
                                Surface :
                                <strong id="surface-preview">
                                    —
                                </strong>
                            </p>


                            <div id="panel-form-error"></div>


                            <button type="submit">
                                Ajouter
                            </button>

                        </form>

                    </div>
                `)
                .addTo(map);


        setupForm(
            map,
            longitude,
            latitude,
            addPanelButton,
            refreshPanels
        );
    });
}


function setupForm(
    map,
    longitude,
    latitude,
    addPanelButton,
    refreshPanels
) {

    const form =
        document.getElementById("add-panel-form");

    const lengthInput =
        document.getElementById("panel-length");

    const heightInput =
        document.getElementById("panel-height");

    const surfacePreview =
        document.getElementById("surface-preview");


    function updateSurface() {

        const length =
            Number(lengthInput.value);

        const height =
            Number(heightInput.value);


        if (length > 0 && height > 0) {

            const surface =
                length * height;

            surfacePreview.textContent =
                `${surface.toFixed(2)} m²`;

        } else {

            surfacePreview.textContent = "—";
        }
    }


    lengthInput.addEventListener(
        "input",
        updateSurface
    );

    heightInput.addEventListener(
        "input",
        updateSurface
    );


    form.addEventListener(
        "submit",
        async (event) => {

            event.preventDefault();


            const address =
                document.getElementById(
                    "panel-address"
                ).value;

            const addressComplement =
                document.getElementById(
                    "panel-address-complement"
                ).value;


            const length =
                Number(lengthInput.value);

            const height =
                Number(heightInput.value);


            let surface = null;

            if (length > 0 && height > 0) {
                surface = length * height;
            }


            try {

                await createPanel({
                    longitude: longitude,
                    latitude: latitude,
                    address: address,
                    address_complement:
                        addressComplement || null,
                    surface_m2: surface,
                });


                await refreshPanels();


                stopAddPanelMode(
                    map,
                    addPanelButton
                );


            } catch (error) {

                console.error(error);

                document.getElementById(
                    "panel-form-error"
                ).textContent =
                    "Impossible d'ajouter le panneau.";
            }
        }
    );
}