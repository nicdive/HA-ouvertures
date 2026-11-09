"""Intégration Gestion des ouvertures pour Home Assistant."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import CARD_FILENAME, DOMAIN, STATIC_URL_PATH

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
]

WWW_PATH = Path(__file__).parent / "www"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Configure les ressources statiques et la carte Lovelace."""
    hass.data.setdefault(DOMAIN, {})
    await _async_register_frontend(hass)
    return True


async def _async_register_frontend(hass: HomeAssistant) -> None:
    """Enregistre /ouvertures_static et la carte JS."""
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

    card_url = f"{STATIC_URL_PATH}/{CARD_FILENAME}?v=1"
    try:
        from homeassistant.components.frontend import add_extra_js_url

        add_extra_js_url(hass, card_url)
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Impossible d'enregistrer la carte Lovelace : %s", err)
    else:
        _LOGGER.debug("Carte ouvertures enregistrée : %s", card_url)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configure une ouverture."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "data": {**entry.data, **entry.options},
    }

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Décharge une ouverture."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Recharge l'entrée après modification des options."""
    hass.data[DOMAIN][entry.entry_id] = {
        "data": {**entry.data, **entry.options},
    }
    await hass.config_entries.async_reload(entry.entry_id)
