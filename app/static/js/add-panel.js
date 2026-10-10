import { ApiError, createPanel, fetchCommune } from "./api.js";

let addPanelMode = false;
let currentPopup = null;

export function isAddPanelMode() {
    return addPanelMode;
}

function setMode(map, button, enabled) {
    addPanelMode = enabled;
    button.textContent = enabled ? "Annuler" : "+ Ajouter un panneau";
    button.setAttribute("aria-pressed", String(enabled));
    map.getCanvas().style.cursor = enabled ? "crosshair" : "";
}

function stopAddPanelMode(map, button) {
    setMode(map, button, false);
    if (currentPopup) {
        const popup = currentPopup;
        currentPopup = null;
        popup.remove();
    }
}

/** Active le mode de placement d'un panneau sur la carte. */
export function setupAddPanel(map, maplibregl, refreshPanels) {
    const button = document.getElementById("add-panel-button");
    if (!button) {
        console.error('[add-panel] Bouton #add-panel-button introuvable dans le HTML');
        return;
    }
    button.setAttribute("aria-pressed", "false");
    button.addEventListener("click", () => {
        if (addPanelMode) stopAddPanelMode(map, button);
        else setMode(map, button, true);
    });

    map.on("click", async event => {
        if (!addPanelMode || currentPopup) return;

        // Évite d'ajouter par erreur un nouveau panneau en cliquant sur un
        // panneau existant alors que le mode ajout est actif.
        if (map.getLayer("panels-points") &&
            map.queryRenderedFeatures(event.point, { layers: ["panels-points"] }).length > 0) {
            return;
        }

        const longitude = event.lngLat.lng;
        const latitude = event.lngLat.lat;
        const popup = new maplibregl.Popup({
            maxWidth: "460px",
            className: "add-panel-popup-container",
            closeOnClick: false,
        }).setLngLat([longitude, latitude]).setHTML(`
            <div class="add-panel-popup">
                <header class="add-panel-header">
                    <h2>Ajouter un panneau</h2>
                    <p>Position sélectionnée sur la carte</p>
                </header>
                <div class="commune-info">
                    <span aria-hidden="true">📍</span>
                    <div>
                        <strong class="panel-commune">Recherche de la commune...</strong>
                        <small>Détection automatique depuis les coordonnées</small>
                    </div>
                </div>
                <form class="add-panel-form">
                    <div class="form-field">
                        <label for="panel-address">Adresse</label>
                        <input id="panel-address" class="panel-address" type="text"
                               placeholder="Ex. 12 rue de Lille" maxlength="500" required>
                    </div>
                    <div class="form-field">
                        <label for="panel-address-complement">Précision sur l'emplacement</label>
                        <input id="panel-address-complement" class="panel-address-complement"
                               type="text" placeholder="Ex. mur à gauche de la mairie" maxlength="500">
                    </div>
                    <div class="dimensions-row">
                        <div class="form-field">
                            <label for="panel-length">Largeur</label>
                            <div class="input-with-unit">
                                <input id="panel-length" class="panel-length" type="number"
                                       step="any" min="0.01" placeholder="2.0">
                                <span>m</span>
                            </div>
                        </div>
                        <div class="form-field">
                            <label for="panel-height">Hauteur</label>
                            <div class="input-with-unit">
                                <input id="panel-height" class="panel-height" type="number"
                                       step="any" min="0.01" placeholder="1.5">
                                <span>m</span>
                            </div>
                        </div>
                    </div>
                    <div class="surface-preview">
                        <span>Surface estimée</span>
                        <strong class="surface-value">—</strong>
                    </div>
                    <div class="form-error" role="alert"></div>
                    <button class="primary-button" type="submit">Ajouter le panneau</button>
                </form>
            </div>
        `).addTo(map);

        currentPopup = popup;
        popup.on("close", () => {
            if (currentPopup !== popup) return;
            currentPopup = null;
            setMode(map, button, false);
        });
        const root = popup.getElement();
        const communeElement = root.querySelector(".panel-commune");
        const submitButton = root.querySelector('button[type="submit"]');
        submitButton.disabled = true; // Attend la validation de la commune.
        setupForm(root, longitude, latitude, map, button, refreshPanels);

        try {
            const commune = await fetchCommune(longitude, latitude);
            if (currentPopup !== popup) return; // Popup fermée entre-temps.
            if (commune) {
                communeElement.textContent = `${commune.commune_name} · ${commune.commune_code}`;
                submitButton.disabled = false;
            } else {
                communeElement.textContent = "Aucune commune trouvée ici";
            }
        } catch (error) {
            console.error("[add-panel] Impossible de détecter la commune", error);
            if (currentPopup === popup) communeElement.textContent =
                "Service de localisation temporairement indisponible";
        }
    });
}

function setupForm(root, longitude, latitude, map, button, refreshPanels) {
    const form = root.querySelector(".add-panel-form");
    const widthInput = root.querySelector(".panel-length");
    const heightInput = root.querySelector(".panel-height");
    const surfacePreview = root.querySelector(".surface-value");
    const errorElement = root.querySelector(".form-error");
    const submitButton = form.querySelector('button[type="submit"]');

    function getSurface() {
        const widthText = widthInput.value.trim();
        const heightText = heightInput.value.trim();
        if (!widthText && !heightText) return null;
        if (!widthText || !heightText) throw new Error("Renseigne les deux dimensions ou aucune.");
        const width = Number(widthText);
        const height = Number(heightText);
        if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) {
            throw new Error("Les dimensions doivent être strictement positives.");
        }
        return width * height;
    }

    function updateSurfacePreview() {
        try {
            const surface = getSurface();
            surfacePreview.textContent = surface == null
                ? "—" : `${surface.toLocaleString("fr-FR", { maximumFractionDigits: 2 })} m²`;
        } catch {
            surfacePreview.textContent = "Dimensions incomplètes";
        }
    }
    widthInput.addEventListener("input", updateSurfacePreview);
    heightInput.addEventListener("input", updateSurfacePreview);

    form.addEventListener("submit", async event => {
        event.preventDefault();
        if (submitButton.disabled) return;
        errorElement.textContent = "";
        let surface;
        try {
            surface = getSurface();
        } catch (error) {
            errorElement.textContent = error.message;
            return;
        }

        const address = root.querySelector(".panel-address").value.trim();
        const addressComplement = root.querySelector(".panel-address-complement").value.trim();
        submitButton.disabled = true;
        submitButton.textContent = "Ajout en cours...";

        try {
            await createPanel({
                longitude,
                latitude,
                address,
                address_complement: addressComplement || null,
                surface_m2: surface,
            });
        } catch (error) {
            console.error("[add-panel] Création refusée", error);
            if (error instanceof ApiError && error.status === 409) {
                errorElement.textContent = "Un panneau existe déjà à moins de 5 mètres.";
            } else if (error instanceof ApiError && error.status === 422) {
                errorElement.textContent = `Données invalides : ${error.message}`;
            } else {
                errorElement.textContent = "Impossible d'ajouter ce panneau. Réessaie.";
            }
            submitButton.disabled = false;
            submitButton.textContent = "Ajouter le panneau";
            return;
        }

        // Création réussie : on ferme, même si le GET suivant échoue.
        // Ne pas afficher « échec de création » pour un échec du refresh.
        stopAddPanelMode(map, button);
        try {
            await refreshPanels();
        } catch (error) {
            console.warn("[add-panel] Panneau enregistré mais carte non actualisée", error);
        }
    });
}
