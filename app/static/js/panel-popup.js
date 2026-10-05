export function showPanelPopup(
    map,
    maplibregl,
    feature
) {

    const coordinates =
        feature.geometry.coordinates.slice();

    const properties =
        feature.properties;


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
}