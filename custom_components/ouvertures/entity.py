"""Entité de base pour les ouvertures."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_call_later, async_track_state_change_event

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

# Ignore les rafales d'updates cover (current_position) → évite le clignotement UI
_DEBOUNCE_SECONDS = 0.35


class OuvertureEntity(Entity):
    """Entité liée à une ouverture configurée."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._data = {**entry.data, **entry.options}
        self._resolved = resolve_opening(hass, self._data)
        self._last_published: tuple | None = None
        self._debounce_unsub = None
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

    def _fingerprint(self) -> tuple:
        r = self._resolved
        return (
            r.get("state"),
            r.get("image"),
            r.get("label"),
            r.get("is_open"),
            r.get("is_alert"),
            r.get("shutter_open"),
        )

    def _publish_if_changed(self) -> None:
        self.refresh_resolved()
        fp = self._fingerprint()
        if fp == self._last_published:
            return
        self._last_published = fp
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        self._last_published = self._fingerprint()
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
        def _flush(_now=None) -> None:
            self._debounce_unsub = None
            self._publish_if_changed()

        @callback
        def _on_state_change(_event: Event) -> None:
            # Debounce : un cover qui remonte la position 10×/s ne doit pas
            # republier l'état combiné tant que open/closed n'a pas changé.
            if self._debounce_unsub is not None:
                self._debounce_unsub()
            self._debounce_unsub = async_call_later(
                self.hass, _DEBOUNCE_SECONDS, _flush
            )

        if tracked:
            self.async_on_remove(
                async_track_state_change_event(self.hass, tracked, _on_state_change)
            )

            def _cancel_debounce() -> None:
                if self._debounce_unsub is not None:
                    self._debounce_unsub()
                    self._debounce_unsub = None

            self.async_on_remove(_cancel_debounce)
