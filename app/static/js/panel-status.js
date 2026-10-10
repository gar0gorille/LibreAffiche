/**
 * Statuts des *affiches*, et non disponibilité physique des panneaux.
 *
 * panels.status : AVAILABLE / UNKNOWN / ... (existence du support).
 * panels.latest_event_type : COVERED / VISIBLE / ... (dernier constat).
 * Seul le dernier événement détermine la couleur d'affichage sur la carte.
 * Conserver les clés en phase avec app.schemas.panel_event.EventType.
 */
export const PANEL_STATUSES = Object.freeze({
    POSTER_ADDED:     { label: "Affiche ajoutée",        color: "#2a9d8f" },
    VISIBLE:          { label: "Visible",               color: "#2a9d8f" },
    PARTIALLY_COVERED:{ label: "Partiellement couvert",color: "#f4a261" },
    COVERED:          { label: "Couvert",               color: "#e63946" },
    EMPTY:            { label: "Vide",                  color: "#6c757d" },
    POSTER_REMOVED:   { label: "Affiche retirée",       color: "#151718" },
});

export const UNKNOWN_STATUS = Object.freeze({
    label: "État non renseigné",
    color: "#457b9d",
});

export function getStatusInfo(eventType) {
    // IMPORTANT : status="AVAILABLE" n'est pas un événement et reste bleu.
    return Object.hasOwn(PANEL_STATUSES, eventType)
        ? PANEL_STATUSES[eventType]
        : UNKNOWN_STATUS;
}

/**
 * Expression MapLibre :
 *  1. feature-state = effet immédiat après un POST réussi ;
 *  2. latest_event_type = donnée pérenne renvoyée par le backend ;
 *  3. status = secours, sans confondre AVAILABLE et VISIBLE ;
 *  4. bleu = aucune information de signalement.
 *
 * Attention : feature-state exige `promoteId: "id"` dans map.addSource().
 * Cette constante ne doit être déclarée qu'UNE seule fois (doublon fatal dans l'original).
 */
export const PANEL_COLOR_EXPRESSION = [
    "match",
    [
        "coalesce",
        ["feature-state", "latest_event_type"],
        ["get", "latest_event_type"],
        ["get", "status"],
    ],
    ...Object.entries(PANEL_STATUSES).flatMap(
        ([eventType, { color }]) => [eventType, color]
    ),
    UNKNOWN_STATUS.color,
];
