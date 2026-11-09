"""Entité de base pour les ouvertures."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_CLOSE_ENTITY,
    CONF_CONTACT_ENTITY,
    CONF_IMPULSE_ENTITY,
    CONF_NAME,
    CONF_OPEN_ENTITY,
    CONF_OPENING_TYPE,
    CONF_SHUTTER_ENTITY,
    DOMAIN,
    OPENING_TYPES,
)
from .helpers import resolve_opening


class OuvertureEntity(Entity):
    """Entité liée à une ouverture configurée."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._data = {**entry.data, **entry.options}
        self._resolved = resolve_opening(hass, self._data)
        name = self._data[CONF_NAME]
        opening_type = self._data[CONF_OPENING_TYPE]
        meta = OPENING_TYPES[opening_type]

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=name,
            manufacturer="Ouvertures",
            model=meta["label"],
            suggested_area=None,
        )
        self._attr_icon = meta["icon"]

    @property
    def entry_data(self) -> dict:
        return {**self._entry.data, **self._entry.options}

    def refresh_resolved(self) -> None:
        self._data = self.entry_data
        self._resolved = resolve_opening(self.hass, self._data)

    async def async_added_to_hass(self) -> None:
        tracked = [
            eid
            for eid in (
                self._data.get(CONF_CONTACT_ENTITY),
                self._data.get(CONF_SHUTTER_ENTITY),
                self._data.get(CONF_OPEN_ENTITY),
                self._data.get(CONF_CLOSE_ENTITY),
                self._data.get(CONF_IMPULSE_ENTITY),
            )
            if eid
        ]

        @callback
        def _on_state_change(_event: Event) -> None:
            self.refresh_resolved()
            self.async_write_ha_state()

        if tracked:
            self.async_on_remove(
                async_track_state_change_event(self.hass, tracked, _on_state_change)
            )
