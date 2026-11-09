"""Boutons de commande (portail / garage)."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_CLOSE_ENTITY,
    CONF_IMPULSE_ENTITY,
    CONF_OPEN_ENTITY,
    CONF_OPENING_TYPE,
    OPENING_TYPES,
)
from .entity import OuvertureEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = {**entry.data, **entry.options}
    meta = OPENING_TYPES[data[CONF_OPENING_TYPE]]
    entities: list[ButtonEntity] = []

    if meta["needs_open"] and data.get(CONF_OPEN_ENTITY):
        entities.append(
            OuvertureActionButton(
                hass, entry, "ouvrir", "Ouvrir", CONF_OPEN_ENTITY, "mdi:gate-open"
            )
        )
    if meta["needs_close"] and data.get(CONF_CLOSE_ENTITY):
        entities.append(
            OuvertureActionButton(
                hass, entry, "fermer", "Fermer", CONF_CLOSE_ENTITY, "mdi:gate"
            )
        )
    if meta["needs_impulse"] and data.get(CONF_IMPULSE_ENTITY):
        entities.append(
            OuvertureActionButton(
                hass,
                entry,
                "impulsion",
                "Impulsion",
                CONF_IMPULSE_ENTITY,
                "mdi:gesture-tap-button",
            )
        )

    if entities:
        async_add_entities(entities)


async def _press_linked_entity(hass: HomeAssistant, entity_id: str) -> None:
    """Déclenche l'entité liée selon son domaine."""
    domain = entity_id.split(".", 1)[0]
    state = hass.states.get(entity_id)

    if domain == "button":
        await hass.services.async_call(
            "button", "press", {"entity_id": entity_id}, blocking=True
        )
    elif domain == "input_button":
        await hass.services.async_call(
            "input_button", "press", {"entity_id": entity_id}, blocking=True
        )
    elif domain == "script":
        await hass.services.async_call(
            "script", "turn_on", {"entity_id": entity_id}, blocking=True
        )
    elif domain == "scene":
        await hass.services.async_call(
            "scene", "turn_on", {"entity_id": entity_id}, blocking=True
        )
    elif domain == "switch":
        await hass.services.async_call(
            "switch", "toggle", {"entity_id": entity_id}, blocking=True
        )
    elif domain == "cover":
        # Si l'entité open/close est un cover, on ouvre ou on ferme
        # selon l'état courant pour l'impulsion ; pour open/close dédiés
        # l'appelant choisit le service via le rôle du bouton.
        current = state.state if state else None
        if current in ("open", "opening"):
            service = "close_cover"
        else:
            service = "open_cover"
        await hass.services.async_call(
            "cover", service, {"entity_id": entity_id}, blocking=True
        )
    else:
        _LOGGER.warning(
            "Domaine non géré pour l'action ouverture : %s (%s)", entity_id, domain
        )


class OuvertureActionButton(OuvertureEntity, ButtonEntity):
    """Bouton qui relaye vers une entité Home Assistant."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        key: str,
        name: str,
        config_key: str,
        icon: str,
    ) -> None:
        super().__init__(hass, entry)
        self._config_key = config_key
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_icon = icon

    async def async_press(self) -> None:
        entity_id = self.entry_data.get(self._config_key)
        if not entity_id:
            _LOGGER.error("Aucune entité configurée pour %s", self._key)
            return

        domain = entity_id.split(".", 1)[0]
        if domain == "cover" and self._key == "ouvrir":
            await self.hass.services.async_call(
                "cover", "open_cover", {"entity_id": entity_id}, blocking=True
            )
            return
        if domain == "cover" and self._key == "fermer":
            await self.hass.services.async_call(
                "cover", "close_cover", {"entity_id": entity_id}, blocking=True
            )
            return
        if domain == "switch" and self._key in ("ouvrir", "fermer"):
            await self.hass.services.async_call(
                "switch", "turn_on", {"entity_id": entity_id}, blocking=True
            )
            return

        await _press_linked_entity(self.hass, entity_id)
