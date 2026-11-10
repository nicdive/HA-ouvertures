"""Intégration Gestion des ouvertures pour Home Assistant."""

from __future__ import annotations

import logging
from pathlib import Path

import asyncio

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, Platform
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import CARD_FILENAME, DOMAIN, STATIC_URL_PATH
from .dashboard import async_setup_dashboard_hooks, schedule_dashboard_update

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
]

WWW_PATH = Path(__file__).parent / "www"
CARD_VERSION = "1.3.6"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Configure les ressources statiques et la carte Lovelace."""
    hass.data.setdefault(DOMAIN, {})
    await _async_register_frontend(hass)
    await async_setup_dashboard_hooks(hass)
    return True


async def _async_register_frontend(hass: HomeAssistant) -> None:
    """Enregistre /ouvertures_static, add_extra_js_url et ressource Lovelace."""
    try:
        from homeassistant.components.http import StaticPathConfig

        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    STATIC_URL_PATH,
                    str(WWW_PATH),
                    cache_headers=False,
                )
            ]
        )
    except Exception:  # noqa: BLE001 — compat anciennes versions HA
        hass.http.async_register_static_path(
            STATIC_URL_PATH,
            str(WWW_PATH),
            cache_headers=False,
        )

    card_url = f"{STATIC_URL_PATH}/{CARD_FILENAME}?v={CARD_VERSION}"

    try:
        from homeassistant.components.frontend import add_extra_js_url

        add_extra_js_url(hass, card_url)
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("add_extra_js_url impossible : %s", err)

    # Ressource Lovelace (module) = indispensable pour le sélecteur de cartes
    async def _register_resource(_event: Event | None = None) -> None:
        await _async_register_lovelace_resource(hass, card_url)

    if hass.is_running:
        hass.async_create_task(_register_resource())
    else:
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _register_resource)

    _LOGGER.debug("Carte ouvertures enregistrée : %s", card_url)


async def _async_register_lovelace_resource(hass: HomeAssistant, url: str) -> None:
    """Ajoute la carte dans Paramètres → Tableaux de bord → Ressources."""
    try:
        from homeassistant.components.lovelace.const import LOVELACE_DATA
    except Exception:  # noqa: BLE001
        _LOGGER.debug("Lovelace indisponible pour enregistrer la ressource")
        return

    # Attendre que lovelace soit prêt
    for _ in range(20):
        if LOVELACE_DATA in hass.data:
            break
        await asyncio.sleep(0.5)
    else:
        _LOGGER.warning("Timeout: Lovelace non prêt, ressource carte non ajoutée")
        return

    lovelace = hass.data[LOVELACE_DATA]
    resources = lovelace.resources

    # YAML resources : lecture seule
    if getattr(resources, "mode", None) == "yaml" or not hasattr(
        resources, "async_create_item"
    ):
        _LOGGER.info(
            "Lovelace en mode YAML : ajoutez manuellement la ressource %s "
            "(type module) dans configuration.yaml",
            url,
        )
        return

    try:
        await resources.async_get_info()
    except Exception:  # noqa: BLE001
        pass

    items = []
    try:
        items = list(resources.async_items())
    except Exception:  # noqa: BLE001
        try:
            data = await resources.async_load(False)  # type: ignore[attr-defined]
            items = list(data) if data else []
        except Exception:  # noqa: BLE001
            items = []

    base = url.split("?", 1)[0]
    for item in items:
        item_url = str(item.get("url", ""))
        if item_url == url or item_url.startswith(base):
            # Mettre à jour le ?v= pour forcer le rechargement
            item_id = item.get("id")
            if item_id and item_url != url and hasattr(resources, "async_update_item"):
                try:
                    await resources.async_update_item(
                        item_id, {"res_type": "module", "url": url}
                    )
                    _LOGGER.info("Ressource Lovelace mise à jour : %s", url)
                except Exception as err:  # noqa: BLE001
                    _LOGGER.debug("Update ressource : %s", err)
            return

    try:
        await resources.async_create_item({"res_type": "module", "url": url})
        _LOGGER.info("Ressource Lovelace créée : %s", url)
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Impossible d'ajouter la ressource Lovelace : %s", err)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configure une ouverture."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "data": {**entry.data, **entry.options},
    }

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await async_setup_dashboard_hooks(hass)
    schedule_dashboard_update(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Décharge une ouverture."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        schedule_dashboard_update(hass)
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Appelé après suppression définitive d'une entrée."""
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    schedule_dashboard_update(hass)


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Recharge l'entrée après modification des options."""
    hass.data[DOMAIN][entry.entry_id] = {
        "data": {**entry.data, **entry.options},
    }
    await hass.config_entries.async_reload(entry.entry_id)
    schedule_dashboard_update(hass)
