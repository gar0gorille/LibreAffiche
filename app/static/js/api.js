/** Fonctions réseau pour les communes et les panneaux (API FastAPI). */

export class ApiError extends Error {
    constructor(status, detail, url) {
        super(detail || `Erreur HTTP ${status}`);
        this.name = "ApiError";
        this.status = status;
        this.url = url;
    }
}

/**
 * Retourne le JSON d'une réponse HTTP ou une ApiError exploitable en UI.
 * FastAPI renvoie souvent { detail: string | Array<ValidationError> }.
 */
export async function requestJson(url, options = {}) {
    const response = await fetch(url, options);
    let data = null;

    try {
        data = await response.json();
    } catch {
        // Réponses d'erreur HTML ou corps vide : on garde le code HTTP.
    }

    if (!response.ok) {
        const detail = data?.detail;
        const message = typeof detail === "string"
            ? detail
            : Array.isArray(detail)
                ? detail.map(item => item.msg ?? "Champ invalide").join(" ; ")
                : `Erreur HTTP ${response.status}`;
        console.error("[api] Échec HTTP", { url, status: response.status, detail });
        throw new ApiError(response.status, message, url);
    }

    return data;
}

export async function fetchCommune(longitude, latitude) {
    // Convention GeoJSON/PostGIS : longitude d'abord, latitude ensuite.
    const params = new URLSearchParams({ lon: longitude, lat: latitude });
    const url = `/communes/?${params}`;

    try {
        return await requestJson(url);
    } catch (error) {
        // 404 est normal hors d'une commune connue ; autres erreurs remontées.
        if (error instanceof ApiError && error.status === 404) return null;
        throw error;
    }
}

export function fetchPanels(minLon, minLat, maxLon, maxLat) {
    const params = new URLSearchParams({
        min_lon: minLon,
        min_lat: minLat,
        max_lon: maxLon,
        max_lat: maxLat,
    });
    return requestJson(`/panels/?${params}`);
}

export function createPanel(panel) {
    // PanelCreate exige longitude, latitude ; adresse et surface facultatives.
    return requestJson("/panels/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(panel),
    });
}

// Compatibilité avec les anciens imports venant de './api.js'.
// Une seule implémentation des événements vit désormais dans panel-events.js.
export { fetchPanelEvents, createPanelEvent } from "./panel-events.js";
