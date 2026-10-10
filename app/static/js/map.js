import * as maplibregl from "https://unpkg.com/maplibre-gl@^6.11.2/dist/maplibre-gl.mjs";
import { fetchPanels } from "./api.js";
import { setupAddPanel, isAddPanelMode } from "./add-panel.js";
import { PANEL_COLOR_EXPRESSION, PANEL_STATUSES, UNKNOWN_STATUS } from "./panel-status.js";
import { showPanelPopup } from "./panel-popup.js";

const SOURCE_ID = "panels";
const LAYER_ID = "panels-points";

const map = new maplibregl.Map({
    container: "map",
    style: "https://tiles.openfreemap.org/styles/liberty",
    center: [3.16, 50.69], // Roubaix : position initiale, à rendre configurable plus tard.
    zoom: 13,
});
map.addControl(new maplibregl.NavigationControl(), "top-right");

let requestSequence = 0;
// Couleurs affichées immédiatement, avant confirmation par GET /panels/.
const pendingStatuses = new Map();

/**
 * Recharge les panneaux visibles sans laisser une ancienne réponse réseau
 * écraser une réponse plus récente si l'utilisateur déplace la carte rapidement.
 */
async function refreshPanels() {
    const source = map.getSource(SOURCE_ID);
    if (!source) return null; // Première requête : attendre l'initialisation.

    const sequence = ++requestSequence;
    const bounds = map.getBounds();
    const geojson = await fetchPanels(
        bounds.getWest(), bounds.getSouth(),
        bounds.getEast(), bounds.getNorth()
    );

    if (sequence !== requestSequence) {
        console.debug("[map] Réponse obsolète ignorée", sequence);
        return null;
    }

    source.setData(geojson);

    // Une fois le dernier événement confirmé par la base, on supprime la
    // surcharge feature-state APRÈS le traitement du nouveau GeoJSON.
    // Sans cette attente, la couleur peut revenir brièvement à l'ancien état.
    for (const feature of geojson.features ?? []) {
        const id = String(feature.properties?.id ?? "");
        const pending = pendingStatuses.get(id);
        if (!pending || pending !== feature.properties?.latest_event_type) continue;

        map.once("idle", () => {
            if (pendingStatuses.get(id) !== pending) return;
            pendingStatuses.delete(id);
            map.removeFeatureState(
                { source: SOURCE_ID, id },
                "latest_event_type"
            );
            console.debug("[map] Dernier événement confirmé par l'API", { id, pending });
        });
    }

    return geojson;
}

/**
 * Après POST /events/ 201 : priorité immédiate à l'état local.
 * Source promoteId="id" indispensable au fonctionnement de setFeatureState.
 * Un F5 revient à la valeur persistée en base (latest_event_type).
 */
function updatePanelStatusImmediately(panelId, eventType) {
    const id = String(panelId);
    pendingStatuses.set(id, eventType);
    if (!map.getSource(SOURCE_ID)) return;
    map.setFeatureState(
        { source: SOURCE_ID, id },
        { latest_event_type: eventType }
    );
    console.debug("[map] Couleur actualisée immédiatement", { id, eventType });
}

function addMapLegend() {
    const entries = [
        PANEL_STATUSES.VISIBLE,
        PANEL_STATUSES.PARTIALLY_COVERED,
        PANEL_STATUSES.COVERED,
        PANEL_STATUSES.EMPTY,
        PANEL_STATUSES.POSTER_REMOVED,
        UNKNOWN_STATUS,
    ];

    const control = {
        onAdd() {
            const container = document.createElement("div");
            container.className = "maplibregl-ctrl panel-legend";
            const button = document.createElement("button");
            button.type = "button";
            button.className = "legend-toggle";
            button.textContent = "Légende";
            button.setAttribute("aria-expanded", "false");
            const content = document.createElement("div");
            content.className = "legend-content";
            content.hidden = true;
            for (const entry of entries) {
                const item = document.createElement("div");
                item.className = "legend-item";
                const dot = document.createElement("span");
                dot.className = "legend-dot";
                dot.style.backgroundColor = entry.color;
                const label = document.createElement("span");
                label.textContent = entry.label;
                item.append(dot, label);
                content.append(item);
            }
            button.addEventListener("click", () => {
                content.hidden = !content.hidden;
                button.textContent = content.hidden ? "Légende" : "Fermer";
                button.setAttribute("aria-expanded", String(!content.hidden));
            });
            container.append(button, content);
            this.container = container;
            return container;
        },
        onRemove() {
            this.container?.remove();
            this.container = null;
        },
    };
    map.addControl(control, "top-left");
}

map.on("load", async () => {
    // Ajouter la source AVANT la première requête : sinon setData ne fait rien.
    map.addSource(SOURCE_ID, {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
        promoteId: "id", // properties.id (UUID ou chaîne issu des imports).
    });
    map.addLayer({
        id: LAYER_ID,
        source: SOURCE_ID,
        type: "circle",
        paint: {
            "circle-radius": 7,
            "circle-color": PANEL_COLOR_EXPRESSION,
            "circle-stroke-width": 2,
            "circle-stroke-color": "#ffffff",
        },
    });
    addMapLegend();

    map.on("click", LAYER_ID, (event) => {
        if (isAddPanelMode() || !event.features?.[0]) return;
        showPanelPopup(
            map, maplibregl, event.features[0],
            refreshPanels, updatePanelStatusImmediately
        );
    });
    map.on("mouseenter", LAYER_ID, () => {
        if (!isAddPanelMode()) map.getCanvas().style.cursor = "pointer";
    });
    map.on("mouseleave", LAYER_ID, () => {
        if (!isAddPanelMode()) map.getCanvas().style.cursor = "";
    });

    try {
        await refreshPanels();
    } catch (error) {
        console.error("[map] Impossible de charger les panneaux initiaux", error);
    }
});

map.on("moveend", () => {
    if (!map.getSource(SOURCE_ID)) return;
    refreshPanels().catch(error => {
        console.error("[map] Échec du rafraîchissement après déplacement", error);
    });
});

// Le module s'enregistre même avant l'événement 'load', ce qui est normal.
setupAddPanel(map, maplibregl, refreshPanels);
