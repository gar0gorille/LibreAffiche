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


function resetAddPanelMode(map, button) {

    addPanelMode = false;

    button.textContent =
        "+ Ajouter un panneau";

    map.getCanvas().style.cursor = "";
}


function stopAddPanelMode(map, button) {

    resetAddPanelMode(map, button);

    if (currentPopup) {

        const popup = currentPopup;

        currentPopup = null;

        popup.remove();
    }
}


export function setupAddPanel(
    map,
    maplibregl,
    refreshPanels
) {

    const addPanelButton =
        document.getElementById(
            "add-panel-button"
        );


    addPanelButton.addEventListener(
        "click",
        () => {

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
        }
    );


    map.on("click", async (e) => {

        if (!addPanelMode) {
            return;
        }


        // On a déjà choisi un emplacement.
        if (currentPopup) {
            return;
        }


        const longitude =
            e.lngLat.lng;

        const latitude =
            e.lngLat.lat;


        const popup =
            new maplibregl.Popup({
                maxWidth: "460px",
                closeOnClick: false,
                className:
                    "add-panel-popup-container",
            })
                .setLngLat([
                    longitude,
                    latitude
                ])
                .setHTML(`
                <div class="add-panel-popup">

                    <div class="add-panel-header">

                        <h2>
                            Ajouter un panneau
                        </h2>

                        <p>
                            Position sélectionnée sur la carte
                        </p>

                    </div>


                    <div class="commune-info">

                        <span class="commune-icon">
                            📍
                        </span>

                        <div>

                            <strong id="panel-commune">
                                Recherche de la commune...
                            </strong>

                            <small>
                                Détection automatique
                            </small>

                        </div>

                    </div>


                    <form id="add-panel-form">

                        <div class="form-field">

                            <label for="panel-address">
                                Adresse
                            </label>

                            <input
                                id="panel-address"
                                type="text"
                                placeholder="Ex. 12 rue de Lille"
                                required
                            >

                        </div>


                        <div class="form-field">

                            <label for="panel-address-complement">
                                Précision sur l'emplacement
                            </label>

                            <input
                                id="panel-address-complement"
                                type="text"
                                placeholder="Ex. mur à gauche de la mairie"
                            >

                        </div>


                        <div class="dimensions-row">

                            <div class="form-field">

                                <label for="panel-length">
                                    Largeur
                                </label>

                                <div class="input-with-unit">

                                    <input
                                        id="panel-length"
                                        type="number"
                                        step="0.1"
                                        min="0"
                                        placeholder="2.0"
                                    >

                                    <span>m</span>

                                </div>

                            </div>


                            <div class="form-field">

                                <label for="panel-height">
                                    Hauteur
                                </label>

                                <div class="input-with-unit">

                                    <input
                                        id="panel-height"
                                        type="number"
                                        step="0.1"
                                        min="0"
                                        placeholder="1.5"
                                    >

                                    <span>m</span>

                                </div>

                            </div>

                        </div>


                        <div class="surface-preview">

                            <span>
                                Surface estimée
                            </span>

                            <strong id="surface-preview">
                                —
                            </strong>

                        </div>


                        <div
                            id="panel-form-error"
                            class="form-error"
                            role="alert"
                        ></div>


                        <button
                            id="submit-panel-button"
                            class="primary-button"
                            type="submit"
                        >
                            Ajouter le panneau
                        </button>

                    </form>

                </div>
            `)
                .addTo(map);


        currentPopup = popup;


        popup.on("close", () => {

            if (currentPopup === popup) {
                currentPopup = null;
            }

            resetAddPanelMode(
                map,
                addPanelButton
            );
        });


        setupForm(
            map,
            longitude,
            latitude,
            addPanelButton,
            refreshPanels
        );


        // Commune chargée après affichage
        // pour ne pas faire attendre l'utilisateur.
        const commune =
            await fetchCommune(
                longitude,
                latitude
            );


        const communeElement =
            document.getElementById(
                "panel-commune"
            );


        if (communeElement) {

            if (commune) {

                communeElement.textContent =
                    `${commune.commune_name} · ${commune.commune_code}`;

            } else {

                communeElement.textContent =
                    "Commune non identifiée";
            }
        }
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
        document.getElementById(
            "add-panel-form"
        );

    const lengthInput =
        document.getElementById(
            "panel-length"
        );

    const heightInput =
        document.getElementById(
            "panel-height"
        );

    const surfacePreview =
        document.getElementById(
            "surface-preview"
        );

    const errorElement =
        document.getElementById(
            "panel-form-error"
        );

    const submitButton =
        document.getElementById(
            "submit-panel-button"
        );


    function updateSurface() {

        const length =
            Number(lengthInput.value);

        const height =
            Number(heightInput.value);


        if (
            length > 0 &&
            height > 0
        ) {

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


            errorElement.textContent = "";

            submitButton.disabled = true;

            submitButton.textContent =
                "Ajout en cours...";


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


            if (
                length > 0 &&
                height > 0
            ) {

                surface =
                    length * height;
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


                errorElement.textContent =
                    "Impossible d'ajouter le panneau. Réessaie.";


                submitButton.disabled = false;

                submitButton.textContent =
                    "Ajouter le panneau";
            }
        }
    );
}