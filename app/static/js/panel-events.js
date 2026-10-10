/**
 * Historique d'un panneau : correspond aux routes du router FastAPI :
 *   GET  /panels/{panel_id}/events/
 *   POST /panels/{panel_id}/events/
 *
 * Ne jamais utiliser l'ancien endpoint /panel-events/?panel_id=...
 */
import { requestJson } from "./api.js";

function eventsUrl(panelId) {
    // encodeURIComponent sécurise l'identifiant dans le chemin de l'URL.
    return `/panels/${encodeURIComponent(String(panelId))}/events/`;
}

export function fetchPanelEvents(panelId) {
    return requestJson(eventsUrl(panelId));
}

export function createPanelEvent(panelId, panelEvent) {
    // Forme attendue par PanelEventCreate : { event_type, comment? }.
    return requestJson(eventsUrl(panelId), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(panelEvent),
    });
}
