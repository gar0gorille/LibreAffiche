export async function fetchCommune(
    longitude,
    latitude
) {

    const params = new URLSearchParams({
        lon: longitude,
        lat: latitude,
    });

    const response = await fetch(
        `/communes/?${params}`
    );

    console.log(
        "Commune request:",
        `/communes/?${params}`
    );

    if (!response.ok) {

        const error = await response.json();

        console.error(
            "Erreur commune:",
            response.status,
            error
        );

        return null;
    }

    return await response.json();
}


export async function fetchPanels(
    minLon,
    minLat,
    maxLon,
    maxLat
) {

    const params = new URLSearchParams({
        min_lon: minLon,
        min_lat: minLat,
        max_lon: maxLon,
        max_lat: maxLat,
    });

    const response = await fetch(
        `/panels/?${params}`
    );

    if (!response.ok) {

        throw new Error(
            `Failed to load panels: ${response.status}`
        );
    }

    return await response.json();
}


export async function createPanel(panel) {

    const response = await fetch(
        "/panels/",
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json",
            },

            body: JSON.stringify(panel),
        }
    );


    if (!response.ok) {

        throw new Error(
            `Impossible d'ajouter le panneau : ${response.status}`
        );
    }

    return await response.json();
}