"""Capteur binaire ouvert / fermé."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_OPENING_TYPE, OPENING_TYPES, TYPE_BAIE, TYPE_GARAGE, TYPE_PORTAIL
from .entity import OuvertureEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([OuvertureOpenBinarySensor(hass, entry)])


class OuvertureOpenBinarySensor(OuvertureEntity, BinarySensorEntity):
    """Indique si l'ouverture est ouverte."""

    _attr_name = "Ouvert"
    _attr_translation_key = "ouvert"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry)
        self._attr_unique_id = f"{entry.entry_id}_ouvert"
        opening_type = self.entry_data[CONF_OPENING_TYPE]
        if opening_type in (TYPE_GARAGE,):
            self._attr_device_class = BinarySensorDeviceClass.GARAGE_DOOR
        elif opening_type in (TYPE_BAIE, TYPE_PORTAIL):
            self._attr_device_class = BinarySensorDeviceClass.DOOR
        else:
            self._attr_device_class = BinarySensorDeviceClass.DOOR

    @property
    def is_on(self) -> bool:
        self.refresh_resolved()
        return bool(self._resolved["is_open"])

    @property
    def icon(self) -> str:
        opening_type = self.entry_data[CONF_OPENING_TYPE]
        base = OPENING_TYPES[opening_type]["icon"]
        if self.is_on:
            if opening_type == TYPE_GARAGE:
                return "mdi:garage-open"
            if opening_type == TYPE_PORTAIL:
                return "mdi:gate-open"
            if opening_type == TYPE_BAIE:
                return "mdi:door-sliding-open"
            return "mdi:door-open"
        return base
