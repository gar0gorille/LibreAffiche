# LibreAffiche — Frontend corrigé et commenté

Ce dossier contient les **6 fichiers JavaScript** et **1 CSS** corrigés, sans changer le contrat HTTP du backend déjà repris lors des étapes précédentes.

## Installation

Copier les fichiers JS dans le dossier où se trouvait votre `map.js` original et le CSS à la place de `map.css`. L'arborescence `app/static/js/` et `app/static/css/` est **proposée** : si votre dépôt utilise une autre structure, conserver la vôtre. Les imports JS (`./api.js`, etc.) supposent que les six modules soient dans le **même dossier**.

Vérifier que votre page HTML référence bien :

```html
<link rel="stylesheet" href="/static/css/map.css">
<div id="map"></div>
<button id="add-panel-button" type="button">+ Ajouter un panneau</button>
<script type="module" src="/static/js/map.js"></script>
```

> Les chemins `/static/...` ne sont que des exemples. Si FastAPI monte les assets à une autre URL, garder vos routes existantes. La feuille CSS de MapLibre GL doit aussi être chargée dans la page HTML, comme auparavant. Il ne faut pas charger `panel-status.js`, `panel-events.js`, etc. séparément comme scripts classiques : ils sont importés comme modules par `map.js`.

## Principaux changements

| Fichier | Modification |
| --- | --- |
| `panel-status.js` | Une seule `PANEL_COLOR_EXPRESSION`, priorité `feature-state → latest_event_type → status → inconnu` ; séparation du statut de support (`AVAILABLE`) et de l'état des affiches (`COVERED`, etc.) |
| `map.js` | Source avant premier chargement, `promoteId: "id"`, `setFeatureState` après un POST, synchronisation après GET, protection contre les réponses réseau arrivant dans le mauvais ordre, légende accessible |
| `panel-events.js` | Routes correctes `/panels/{id}/events/` ; payload conforme à `PanelEventCreate` |
| `api.js` | Factorisation des réponses HTTP, erreurs 404/409/422, export de compatibilité des événements |
| `panel-popup.js` | Historique descendant, XSS évitée via `escapeHtml`, badge réactif, état du formulaire, différence entre échec POST et échec de rafraîchissement |
| `add-panel.js` | Commune vérifiée, détection des dimensions incomplètes, erreurs 409 explicites, sélection impossible sur un point existant, création séparée du rafraîchissement |
| `map.css` | Popup scrollable, largeur mobile, tailles et éléments visuels harmonisés |

## Contrat backend indispensable

Le `GET /panels/?min_lon=...&min_lat=...&max_lon=...&max_lat=...` doit répondre :

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": { "type": "Point", "coordinates": [3.16, 50.69] },
      "properties": {
        "id": "uuid-panneau",
        "status": "AVAILABLE",
        "latest_event_type": "COVERED",
        "latest_event_created_at": "2026-10-10T12:00:00+02:00",
        "address": "...",
        "address_complement": null,
        "surface_m2": 2.0,
        "commune_code": "59512"
      }
    }
  ]
}
```

`POST /panels/{id}/events/` avec `{ "event_type": "COVERED", "comment": null }` doit retourner 201, et le GET GeoJSON suivant doit refléter `latest_event_type: "COVERED"`.

**Attention** : `panels.status = "AVAILABLE"` concerne la disponibilité / existence du support, pas les affiches. La carte met une couleur neutre tant qu'aucun événement d'affichage n'a été signalé.

## Déboguer les couleurs (F12 → Réseau / Console)

1. Ouvrir la carte : vérifier `GET /panels/` -> HTTP 200. Inspecter une `Feature` et son `properties.latest_event_type`.
2. Signaler `COVERED` dans la popup : vérifier `POST /panels/{id}/events/` -> HTTP 201. Le point doit devenir **rouge** tout de suite, indépendamment de la vitesse du GET.
3. Le nouveau `GET /panels/` doit retourner `latest_event_type: "COVERED"`. On attend alors l'événement `idle` de MapLibre avant de retirer la surcharge locale.
4. Faire `F5` : la couleur doit rester rouge. Si elle revient bleue, le **repository / mapper / API** renvoie probablement `null` ou un événement ancien.
5. Si le point ne change pas sans F5, vérifier la Console pour `[map] Couleur actualisée immédiatement` puis inspecter `map.addSource(..., promoteId: "id")` et `properties.id`.

### Tests automatisés

```bash
cd libreaffiche_frontend_corrige
npm test
```

Tests utilisant uniquement `node:test`, sans installation de dépendance supplémentaire. Vérification syntaxique facultative :

```bash
for f in app/static/js/*.js; do node --check "$f"; done
```

**Limites de validation** : les tests Node vérifient les exports, la structure des requêtes, les valeurs de couleur et certains contrats MapLibre. Ils ne remplacent ni des tests de navigateur réel (MapLibre, DOM, scroll) ni un test d'intégration avec la base PostgreSQL/PostGIS.
