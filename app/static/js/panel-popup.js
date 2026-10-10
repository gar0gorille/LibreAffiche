import { PANEL_STATUSES, getStatusInfo } from "./panel-status.js";
import { fetchPanelEvents, createPanelEvent } from "./panel-events.js";

/**
 * Une Feature MapLibre expose des données issues du GeoJSON du mapper.
 * Ne jamais injecter directement les commentaires/adresses utilisateur en HTML.
 */
function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

function formatDate(value) {
    if (!value) return "";
    const date = new Date(value);
    return Number.isNaN(date.getTime())
        ? "Date inconnue"
        : date.toLocaleString("fr-FR", { dateStyle: "short", timeStyle: "short" });
}

function renderHistory(events) {
    if (!Array.isArray(events) || events.length === 0) {
        return '<p class="history-empty">Aucun signalement pour le moment.</p>';
    }
    // L'API renvoie l'ordre chronologique ASC. Les signalements récents en haut.
    return [...events].reverse().map(event => {
        const status = getStatusInfo(event.event_type);
        return `
            <div class="history-event">
                <span class="history-dot" style="background-color:${status.color}"></span>
                <div>
                    <strong>${escapeHtml(status.label)}</strong>
                    <span>${escapeHtml(formatDate(event.created_at))}</span>
                    ${event.comment ? `<p>${escapeHtml(event.comment)}</p>` : ""}
                </div>
            </div>`;
    }).join("");
}

/**
 * Ouvre la fiche d'un panneau et lie ses interactions.
 * refreshPanels : callback asynchrone de map.js (GET GeoJSON).
 * updatePanelStatusImmediately : callback feature-state, appelé APRÈS le POST 201.
 */
export function showPanelPopup(
    map,
    maplibregl,
    feature,
    refreshPanels,
    updatePanelStatusImmediately = () => {}
) {
    const properties = feature?.properties ?? {};
    const panelId = properties.id ?? feature?.id;
    if (!panelId || !Array.isArray(feature?.geometry?.coordinates)) {
        console.error("[panel-popup] Panneau sans identifiant ou coordonnées", feature);
        return null;
    }

    // `status` est l'état du support, pas celui des affiches : n'utiliser le
    // dernier événement que si disponible ; sinon afficher l'état inconnu.
    const status = getStatusInfo(properties.latest_event_type);
    const address = escapeHtml(properties.address || "Adresse inconnue");
    const complement = properties.address_complement
        ? `<p>${escapeHtml(properties.address_complement)}</p>` : "";
    const surfaceValue = Number(properties.surface_m2);
    const surface = properties.surface_m2 != null && Number.isFinite(surfaceValue)
        ? `${surfaceValue.toLocaleString("fr-FR", { maximumFractionDigits: 2 })} m²`
        : "Non renseignée";
    const commune = properties.commune_name || properties.commune_code || "Inconnue";

    // Choix initial volontairement vide pour éviter les signalements accidentels.
    const eventOptions = Object.entries(PANEL_STATUSES).map(([value, info]) =>
        `<option value="${value}">${escapeHtml(info.label)}</option>`
    ).join("");

    const popup = new maplibregl.Popup({
        maxWidth: "420px",
        className: "panel-popup-container",
        closeOnClick: true,
    }).setLngLat(feature.geometry.coordinates.slice()).setHTML(`
        <div class="panel-popup">
            <header class="panel-popup-header">
                <div>
                    <h2>${address}</h2>
                    ${complement}
                </div>
                <span class="status-badge" style="--status-color:${status.color}">
                    ${escapeHtml(status.label)}
                </span>
            </header>
            <div class="panel-details">
                <div class="panel-detail">
                    <span>Surface</span><strong>${escapeHtml(surface)}</strong>
                </div>
                <div class="panel-detail">
                    <span>Commune (nom ou code)</span><strong>${escapeHtml(commune)}</strong>
                </div>
            </div>
            <section class="panel-section">
                <h3>Historique</h3>
                <div class="panel-history" aria-live="polite">Chargement...</div>
            </section>
            <section class="panel-section">
                <h3>Signaler un changement</h3>
                <form class="panel-event-form">
                    <label for="panel-event-type">Nouvel état</label>
                    <select id="panel-event-type" class="panel-event-type" required>
                        <option value="" disabled selected>Choisir un état</option>
                        ${eventOptions}
                    </select>
                    <label for="panel-event-comment">Commentaire (optionnel)</label>
                    <textarea id="panel-event-comment" class="panel-event-comment"
                              rows="2" placeholder="Une précision utile..."></textarea>
                    <div class="panel-event-error" role="alert"></div>
                    <div class="panel-event-feedback" role="status" aria-live="polite"></div>
                    <button type="submit" class="primary-button">Signaler</button>
                </form>
            </section>
        </div>
    `).addTo(map);

    // Rechercher les éléments DANS la popup, jamais via document.querySelector :
    // sinon deux popups contenant les mêmes classes pourraient se mélanger.
    const root = popup.getElement();
    const history = root.querySelector(".panel-history");
    const form = root.querySelector(".panel-event-form");
    const typeInput = root.querySelector(".panel-event-type");
    const commentInput = root.querySelector(".panel-event-comment");
    const errorElement = root.querySelector(".panel-event-error");
    const feedbackElement = root.querySelector(".panel-event-feedback");
    const button = form.querySelector('button[type="submit"]');
    const badge = root.querySelector(".status-badge");

    let closed = false;
    let historySequence = 0;
    popup.on("close", () => { closed = true; });

    async function loadHistory() {
        // Plusieurs chargements peuvent se chevaucher (ouverture + POST).
        // Ne laisser que le plus récent actualiser l'interface.
        const sequence = ++historySequence;
        try {
            const events = await fetchPanelEvents(panelId);
            if (!closed && sequence === historySequence) {
                history.innerHTML = renderHistory(events);
            }
        } catch (error) {
            console.error("[panel-popup] Historique non disponible", error);
            if (!closed && sequence === historySequence) {
                history.textContent = "Impossible de charger l'historique.";
            }
        }
    }

    form.addEventListener("submit", async event => {
        event.preventDefault();
        if (closed || button.disabled) return;
        const eventType = typeInput.value;
        if (!Object.hasOwn(PANEL_STATUSES, eventType)) {
            errorElement.textContent = "Sélectionne un état valide.";
            return;
        }
        errorElement.textContent = "";
        feedbackElement.textContent = "";
        button.disabled = true;
        button.textContent = "Envoi...";

        // Seul le POST peut décider si le signalement a été enregistré.
        // Une erreur de rechargement ultérieure ne doit pas être annoncée
        // comme un échec de création, pour éviter de provoquer des doublons.
        try {
            await createPanelEvent(panelId, {
                event_type: eventType,
                comment: commentInput.value.trim() || null,
            });
        } catch (error) {
            console.error("[panel-popup] Enregistrement impossible", error);
            if (!closed) {
                errorElement.textContent = error.message || "Impossible d'enregistrer le signalement.";
                button.disabled = false;
                button.textContent = "Signaler";
            }
            return;
        }

        // POST 201 reçu : la couleur du cercle + le badge changent immédiatement.
        updatePanelStatusImmediately(panelId, eventType);
        console.debug("[panel-popup] Signalement enregistré", { panelId, eventType });
        if (!closed) {
            const updated = getStatusInfo(eventType);
            badge.textContent = updated.label;
            badge.style.setProperty("--status-color", updated.color);
            commentInput.value = "";
            typeInput.value = "";
            feedbackElement.textContent = "Signalement enregistré.";
            button.disabled = false;
            button.textContent = "Signaler";
        }

        // Réconcilie avec le backend pour la persistance après F5 ; si le GET
        // échoue, le feature-state reste visible mais la donnée sera restaurée
        // au prochain rafraîchissement ou rechargement de la page.
        try {
            await refreshPanels();
        } catch (error) {
            console.warn("[panel-popup] Événement enregistré mais carte non rafraîchie", error);
            if (!closed) feedbackElement.textContent =
                "Enregistré, mais le rafraîchissement de la carte a échoué.";
        }
        await loadHistory();
    });

    void loadHistory();
    return popup;
}
