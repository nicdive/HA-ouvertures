"""Création / mise à jour automatique du tableau de bord Lovelace."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from .const import (
    CONF_NAME,
    CONF_OPENING_TYPE,
    DOMAIN,
    OPENING_TYPES,
    TYPE_BAIE,
    TYPE_FENETRE_DOUBLE,
    TYPE_FENETRE_DOUBLE_VOLETS,
    TYPE_FENETRE_SIMPLE,
    TYPE_FENETRE_SIMPLE_VOLETS,
    TYPE_GARAGE,
    TYPE_PISCINE,
    TYPE_PORTAIL,
    TYPE_PORTE,
)

_LOGGER = logging.getLogger(__name__)

DASHBOARD_URL_PATH = "ha-ouvertures"
DASHBOARD_TITLE = "Ouvertures"
DASHBOARD_ICON = "mdi:door-sliding"
NO_AREA = "Sans pièce"

_TYPE_ORDER = (
    TYPE_BAIE,
    TYPE_FENETRE_SIMPLE,
    TYPE_FENETRE_SIMPLE_VOLETS,
    TYPE_FENETRE_DOUBLE,
    TYPE_FENETRE_DOUBLE_VOLETS,
    TYPE_PORTE,
    TYPE_PORTAIL,
    TYPE_GARAGE,
    TYPE_PISCINE,
)

_lock: asyncio.Lock | None = None
_pending: asyncio.TimerHandle | None = None


def _get_lock() -> asyncio.Lock:
    global _lock
    if _lock is None:
        _lock = asyncio.Lock()
    return _lock


def schedule_dashboard_update(hass: HomeAssistant, delay: float = 1.0) -> None:
    """Regroupe plusieurs changements (démarrage / multi-entrées) en une MAJ."""

    def _run() -> None:
        global _pending
        _pending = None
        hass.async_create_task(_async_update_dashboard(hass))

    global _pending
    if _pending is not None:
        _pending.cancel()
    _pending = hass.loop.call_later(delay, _run)


async def async_setup_dashboard_hooks(hass: HomeAssistant) -> None:
    """Enregistre le hook de démarrage (une seule fois)."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get("dashboard_hooks"):
        return
    domain_data["dashboard_hooks"] = True

    if hass.is_running:
        schedule_dashboard_update(hass, delay=2.0)
    else:

        @callback
        def _on_started(_event: Event) -> None:
            schedule_dashboard_update(hass, delay=2.0)

        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _on_started)


def _sensor_entity_id(hass: HomeAssistant, entry: ConfigEntry) -> str | None:
    registry = er.async_get(hass)
    return registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_etat")


def _collect_openings(hass: HomeAssistant) -> list[dict[str, str]]:
    """Liste les ouvertures avec nom / pièce / type."""
    items: list[dict[str, str]] = []

    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.entry_id not in hass.data.get(DOMAIN, {}):
            continue
        opening_type = entry.data.get(CONF_OPENING_TYPE)
        if opening_type not in OPENING_TYPES:
            continue
        entity_id = _sensor_entity_id(hass, entry)
        if not entity_id:
            continue
        state = hass.states.get(entity_id)
        area = ""
        if state:
            area = state.attributes.get("area") or ""
        items.append(
            {
                "entity_id": entity_id,
                "name": entry.data.get(CONF_NAME, entity_id),
                "opening_type": opening_type,
                "area": area,
            }
        )

    items.sort(
        key=lambda i: (
            (i["area"] or "zzz").lower(),
            _TYPE_ORDER.index(i["opening_type"])
            if i["opening_type"] in _TYPE_ORDER
            else 99,
            i["name"].lower(),
        )
    )
    return items


def _dense_card(
    entities: list[str],
    *,
    show_area: bool = False,
    title: str | None = None,
) -> dict[str, Any]:
    """Une carte dense : grille interne (3×n sur mobile), une tuile par ouverture."""
    card: dict[str, Any] = {
        "type": "custom:ouvertures-card",
        "entities": entities,
        "compact": True,
        "show_area": show_area,
        "columns": 3,
    }
    if title:
        card["title"] = title
    return card


def _build_config(items: list[dict[str, str]]) -> dict[str, Any]:
    """Dashboard par pièce : une carte dense par pièce (tuiles séparées en grille)."""
    sections: list[dict[str, Any]] = []

    if items:
        by_area: dict[str, list[dict[str, str]]] = {}
        for item in items:
            key = item.get("area") or NO_AREA
            by_area.setdefault(key, []).append(item)

        area_names = sorted(
            by_area.keys(),
            key=lambda a: (a == NO_AREA, a.lower()),
        )

        for area_name in area_names:
            area_items = by_area[area_name]
            sections.append(
                {
                    "type": "grid",
                    "cards": [
                        {
                            "type": "heading",
                            "heading": area_name,
                            "heading_style": "title",
                            "icon": "mdi:floor-plan",
                        },
                        _dense_card(
                            [i["entity_id"] for i in area_items],
                            show_area=False,
                        ),
                    ],
                }
            )

    if not sections:
        sections = [
            {
                "type": "grid",
                "cards": [
                    {
                        "type": "markdown",
                        "content": (
                            "## Aucune ouverture\n\n"
                            "Ajoutez une baie, porte, portail, garage ou piscine via\n"
                            "**Paramètres → Appareils et services → Gestion des ouvertures**.\n\n"
                            "Astuce : assignez une **pièce** (area) au capteur d'ouverture "
                            "pour organiser le tableau de bord par pièce."
                        ),
                    }
                ],
            }
        ]

    overview_cards: list[dict[str, Any]] = [
        {
            "type": "heading",
            "heading": "Toutes les ouvertures",
            "heading_style": "title",
            "icon": "mdi:view-grid",
        }
    ]
    if items:
        overview_cards.append(
            _dense_card(
                [i["entity_id"] for i in items],
                show_area=True,
            )
        )
    else:
        overview_cards.append(
            {
                "type": "markdown",
                "content": "_Aucune ouverture configurée._",
            }
        )

    return {
        "views": [
            {
                "title": "Par pièce",
                "path": "ouvertures",
                "icon": DASHBOARD_ICON,
                "type": "sections",
                "max_columns": 4,
                "dense": True,
                "sections": sections,
            },
            {
                "title": "Vue d'ensemble",
                "path": "apercu",
                "icon": "mdi:view-grid",
                "type": "sections",
                "max_columns": 4,
                "dense": True,
                "sections": [
                    {
                        "type": "grid",
                        "cards": overview_cards,
                    }
                ],
            },
        ]
    }


def _unwrap_handler(handler: Any) -> Any:
    """Déballe require_admin / async_response pour retrouver la méthode liée."""
    seen: set[int] = set()
    current = handler
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if hasattr(current, "__self__") and hasattr(
            current.__self__, "storage_collection"
        ):
            return current
        current = getattr(current, "__wrapped__", None)
    return None


def _get_official_dashboards_collection(hass: HomeAssistant) -> Any | None:
    """Récupère la DashboardsCollection officielle via le handler websocket."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if (cached := domain_data.get("dashboards_collection")) is not None:
        return cached

    ws_domain = hass.data.get("websocket_api")
    if not isinstance(ws_domain, dict):
        return None

    entry = ws_domain.get("lovelace/dashboards/create")
    if not entry:
        return None

    handler = entry[0]
    bound = _unwrap_handler(handler)
    if bound is None:
        return None

    collection = bound.__self__.storage_collection
    domain_data["dashboards_collection"] = collection
    return collection


async def _async_update_dashboard(hass: HomeAssistant) -> None:
    """Crée ou met à jour le dashboard géré par l'intégration."""
    async with _get_lock():
        try:
            await _async_update_dashboard_locked(hass)
        except Exception:  # noqa: BLE001
            _LOGGER.exception(
                "Impossible de créer/mettre à jour le tableau de bord Ouvertures"
            )


async def _async_update_dashboard_locked(hass: HomeAssistant) -> None:
    from homeassistant.components.lovelace.const import LOVELACE_DATA
    from homeassistant.exceptions import HomeAssistantError
    import voluptuous as vol

    if LOVELACE_DATA not in hass.data:
        _LOGGER.debug("Lovelace absent — nouvelle tentative plus tard")
        schedule_dashboard_update(hass, delay=5.0)
        return

    collection = _get_official_dashboards_collection(hass)
    if collection is None:
        _LOGGER.debug(
            "Collection dashboards Lovelace indisponible — nouvelle tentative"
        )
        schedule_dashboard_update(hass, delay=5.0)
        return

    items = _collect_openings(hass)
    has_any = bool(items)
    lovelace_data = hass.data[LOVELACE_DATA]

    existing = None
    for item in collection.async_items():
        if item.get("url_path") == DASHBOARD_URL_PATH:
            existing = item
            break

    if not has_any:
        if existing is not None:
            try:
                await collection.async_delete_item(existing["id"])
                _LOGGER.info(
                    "Tableau de bord Ouvertures retiré (plus d'ouvertures)"
                )
            except Exception:  # noqa: BLE001
                _LOGGER.debug("Suppression dashboard impossible", exc_info=True)
        return

    if existing is None:
        try:
            existing = await collection.async_create_item(
                {
                    "icon": DASHBOARD_ICON,
                    "title": DASHBOARD_TITLE,
                    "url_path": DASHBOARD_URL_PATH,
                    "require_admin": False,
                    "show_in_sidebar": True,
                }
            )
            _LOGGER.info("Tableau de bord créé : /%s", DASHBOARD_URL_PATH)
        except (HomeAssistantError, vol.Invalid) as err:
            _LOGGER.warning("Création du dashboard impossible : %s", err)
            existing = None
            for item in collection.async_items():
                if item.get("url_path") == DASHBOARD_URL_PATH:
                    existing = item
                    break
            if existing is None and DASHBOARD_URL_PATH in lovelace_data.dashboards:
                store = lovelace_data.dashboards[DASHBOARD_URL_PATH]
                await store.async_save(_build_config(items))
                return
            if existing is None:
                return

    store = lovelace_data.dashboards.get(DASHBOARD_URL_PATH)
    if store is None:
        await asyncio.sleep(0.2)
        store = lovelace_data.dashboards.get(DASHBOARD_URL_PATH)

    if store is None:
        _LOGGER.warning(
            "Dashboard %s créé mais non enregistré dans Lovelace",
            DASHBOARD_URL_PATH,
        )
        return

    await store.async_save(_build_config(items))
    _LOGGER.debug(
        "Tableau de bord Ouvertures mis à jour (%s ouverture(s))",
        len(items),
    )
