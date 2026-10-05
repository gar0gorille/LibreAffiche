// panel-status.js

export const PANEL_STATUSES = {
    POSTER_ADDED: {
        label: "Affiche ajoutée",
        color: "#2a9d8f",
    },

    VISIBLE: {
        label: "Visible",
        color: "#2a9d8f",
    },

    PARTIALLY_COVERED: {
        label: "Partiellement couvert",
        color: "#f4a261",
    },

    COVERED: {
        label: "Couvert",
        color: "#e63946",
    },

    EMPTY: {
        label: "Vide",
        color: "#6c757d",
    },

    POSTER_REMOVED: {
        label: "Affiche retirée",
        color: "#151718",
    },
};


export const UNKNOWN_STATUS = {
    label: "Statut inconnu",
    color: "#457b9d",
};


export function getStatusInfo(status) {

    return PANEL_STATUSES[status]
        ?? UNKNOWN_STATUS;
}


export const PANEL_COLOR_EXPRESSION = [
    "match",
    ["get", "status"],

    ...Object.entries(PANEL_STATUSES)
        .flatMap(
            ([status, config]) => [
                status,
                config.color
            ]
        ),

    UNKNOWN_STATUS.color
];