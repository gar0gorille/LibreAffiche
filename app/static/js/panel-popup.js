import {
    getStatusInfo
} from "./panel-status.js";


function escapeHtml(value) {

    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


export function showPanelPopup(
    map,
    maplibregl,
    feature
) {

    const coordinates =
        feature.geometry.coordinates.slice();

    const properties =
        feature.properties;


    const status =
        getStatusInfo(
            properties.status
        );


    const address =
        properties.address
            ? escapeHtml(properties.address)
            : "Adresse inconnue";


    const addressComplement =
        properties.address_complement
            ? escapeHtml(
                properties.address_complement
            )
            : null;


    const surface =
        properties.surface_m2
            ? `${Number(
                properties.surface_m2
            ).toFixed(2)} m²`
            : "Non renseignée";


    new maplibregl.Popup({
        maxWidth: "380px",
        className:
            "panel-popup-container",
    })
        .setLngLat(coordinates)
        .setHTML(`
            <div class="panel-popup">

                <div class="panel-popup-header">

                    <div>

                        <h2>
                            ${address}
                        </h2>

                        ${addressComplement
                ? `
                                    <p>
                                        ${addressComplement}
                                    </p>
                                `
                : ""
            }

                    </div>


                    <span
                        class="status-badge"
                        style="
                            --status-color:
                            ${status.color};
                        "
                    >
                        ${status.label}
                    </span>

                </div>


                <div class="panel-details">

                    <div class="panel-detail">

                        <span>
                            Surface
                        </span>

                        <strong>
                            ${surface}
                        </strong>

                    </div>


                    ${properties.commune_name
                ? `
                                <div class="panel-detail">

                                    <span>
                                        Commune
                                    </span>

                                    <strong>
                                        ${escapeHtml(
                    properties.commune_name
                )}
                                    </strong>

                                </div>
                            `
                : ""
            }


                    ${properties.source
                ? `
                                <div class="panel-detail">

                                    <span>
                                        Source
                                    </span>

                                    <strong>
                                        ${escapeHtml(
                    properties.source
                )}
                                    </strong>

                                </div>
                            `
                : ""
            }

                </div>

            </div>
        `)
        .addTo(map);
}