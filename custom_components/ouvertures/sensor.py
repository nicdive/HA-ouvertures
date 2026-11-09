"""Capteur d'état combiné des ouvertures."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_AREA,
    ATTR_CLOSE_ENTITY,
    ATTR_CONTACT_ENTITY,
    ATTR_DISPLAY_NAME,
    ATTR_IMAGE,
    ATTR_IMPULSE_ENTITY,
    ATTR_IS_ALERT,
    ATTR_IS_OPEN,
    ATTR_LABEL,
    ATTR_OPEN_ENTITY,
    ATTR_OPENING_TYPE,
    ATTR_SHUTTER_ENTITY,
    ATTR_SHUTTER_OPEN,
    CONF_NAME,
    CONF_OPENING_TYPE,
    DOMAIN,
    OPENING_TYPES,
)
from .entity import OuvertureEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([OuvertureStateSensor(hass, entry)])


class OuvertureStateSensor(OuvertureEntity, SensorEntity):
    """État combiné (texte) d'une ouverture."""

    _attr_translation_key = "etat"
    _attr_name = "État"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry)
        self._attr_unique_id = f"{entry.entry_id}_etat"

    @property
    def native_value(self) -> str:
        self.refresh_resolved()
        return self._resolved["state"]

    @property
    def extra_state_attributes(self) -> dict:
        self.refresh_resolved()
        r = self._resolved
        return {
            ATTR_LABEL: r["label"],
            ATTR_IMAGE: r["image"],
            ATTR_IS_OPEN: r["is_open"],
            ATTR_IS_ALERT: r["is_alert"],
            ATTR_SHUTTER_OPEN: r["shutter_open"],
            ATTR_OPENING_TYPE: r["opening_type"],
            ATTR_CONTACT_ENTITY: r["contact_entity"],
            ATTR_SHUTTER_ENTITY: r["shutter_entity"],
            ATTR_OPEN_ENTITY: r["open_entity"],
            ATTR_CLOSE_ENTITY: r["close_entity"],
            ATTR_IMPULSE_ENTITY: r["impulse_entity"],
            ATTR_AREA: r.get("area"),
            ATTR_DISPLAY_NAME: r.get("display_name") or self.entry_data[CONF_NAME],
            "friendly_state": r["label"],
            "name": self.entry_data[CONF_NAME],
            "type_label": OPENING_TYPES[self.entry_data[CONF_OPENING_TYPE]]["label"],
        }

    @property
    def icon(self) -> str:
        opening_type = self.entry_data[CONF_OPENING_TYPE]
        if self._resolved.get("is_alert"):
            return "mdi:alert"
        return OPENING_TYPES[opening_type]["icon"]
