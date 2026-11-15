"""Alerte « baie / fenêtre restée ouverte » via lumière gateway Xiaomi."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_ALERT_BRIGHTNESS,
    CONF_ALERT_COLOR,
    CONF_ALERT_ENABLED,
    CONF_ALERT_GATEWAY,
    CONF_ALERT_MONITORED,
    CONF_ALERT_TRIGGER,
    CONF_CONTACT_ENTITY,
    CONF_INVERTED,
    CONF_NAME,
    CONF_OPENING_TYPE,
    DOMAIN,
    TYPES_ALERT_MONITORABLE,
    TYPES_ALERT_TRIGGER,
)
from .helpers import is_entity_open

_LOGGER = logging.getLogger(__name__)

DATA_ALERT_MANAGER = "alert_manager"


def _entry_data(entry: ConfigEntry) -> dict[str, Any]:
    return {**entry.data, **entry.options}


def _rgb(color: Any) -> list[int]:
    if isinstance(color, (list, tuple)) and len(color) >= 3:
        try:
            return [max(0, min(255, int(c))) for c in color[:3]]
        except (TypeError, ValueError):
            pass
    return [255, 40, 0]


def _brightness(raw: Any) -> int:
    try:
        return max(1, min(255, int(raw)))
    except (TypeError, ValueError):
        return 180


def opening_contact_open(hass: HomeAssistant, entry: ConfigEntry) -> bool | None:
    """True/False/None selon le contact seul (volets ignorés)."""
    data = _entry_data(entry)
    contact_id = data.get(CONF_CONTACT_ENTITY)
    if not contact_id:
        return None
    inverted = bool(data.get(CONF_INVERTED, False))
    return is_entity_open(hass.states.get(contact_id), inverted)


def list_opening_options(
    hass: HomeAssistant,
    *,
    allowed_types: frozenset[str],
) -> list[dict[str, str]]:
    """Options {value,label} pour les sélecteurs config flow."""
    from .const import OPENING_TYPES

    options: list[dict[str, str]] = []
    for entry in hass.config_entries.async_entries(DOMAIN):
        otype = entry.data.get(CONF_OPENING_TYPE)
        if otype not in allowed_types:
            continue
        name = entry.data.get(CONF_NAME) or entry.title or entry.entry_id
        type_label = OPENING_TYPES.get(otype, {}).get("label", otype)
        label = f"{name} — {type_label}"
        options.append({"value": entry.entry_id, "label": label})
    options.sort(key=lambda o: o["label"].lower())
    return options


class LeftOpenAlertManager:
    """Surveille porte déclencheur + baies/fenêtres ; pilote la gateway."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._unsub = None
        self._active = False
        self._listeners: list[Any] = []

    @property
    def data(self) -> dict[str, Any]:
        return _entry_data(self.entry)

    @property
    def enabled(self) -> bool:
        return bool(self.data.get(CONF_ALERT_ENABLED, True))

    @property
    def is_active(self) -> bool:
        return self._active

    def open_monitored_names(self) -> list[str]:
        names: list[str] = []
        for entry_id in self.data.get(CONF_ALERT_MONITORED) or []:
            entry = self.hass.config_entries.async_get_entry(entry_id)
            if entry is None:
                continue
            if opening_contact_open(self.hass, entry) is True:
                names.append(entry.data.get(CONF_NAME) or entry.title or entry_id)
        return names

    async def async_start(self) -> None:
        await self.async_stop()
        entities = self._tracked_entities()
        if entities:

            @callback
            def _on_change(_event: Event) -> None:
                self.hass.async_create_task(self.async_evaluate())

            self._unsub = async_track_state_change_event(
                self.hass, entities, _on_change
            )
        await self.async_evaluate(initial=True)

    async def async_stop(self) -> None:
        if self._unsub is not None:
            self._unsub()
            self._unsub = None
        for unsub in self._listeners:
            unsub()
        self._listeners.clear()
        if self._active:
            self._active = False
            await self._async_set_light(False)

    def _tracked_entities(self) -> list[str]:
        ids: list[str] = []
        data = self.data
        trigger_id = data.get(CONF_ALERT_TRIGGER)
        if trigger_id:
            trigger = self.hass.config_entries.async_get_entry(trigger_id)
            if trigger and trigger.data.get(CONF_CONTACT_ENTITY):
                ids.append(trigger.data[CONF_CONTACT_ENTITY])
        for entry_id in data.get(CONF_ALERT_MONITORED) or []:
            mon = self.hass.config_entries.async_get_entry(entry_id)
            if mon and mon.data.get(CONF_CONTACT_ENTITY):
                ids.append(mon.data[CONF_CONTACT_ENTITY])
        # unique preserve order
        seen: set[str] = set()
        out: list[str] = []
        for eid in ids:
            if eid not in seen:
                seen.add(eid)
                out.append(eid)
        return out

    def _any_monitored_open(self) -> bool:
        for entry_id in self.data.get(CONF_ALERT_MONITORED) or []:
            entry = self.hass.config_entries.async_get_entry(entry_id)
            if entry is None:
                continue
            if entry.data.get(CONF_OPENING_TYPE) not in TYPES_ALERT_MONITORABLE:
                continue
            if opening_contact_open(self.hass, entry) is True:
                return True
        return False

    def _trigger_open(self) -> bool | None:
        trigger_id = self.data.get(CONF_ALERT_TRIGGER)
        if not trigger_id:
            return None
        entry = self.hass.config_entries.async_get_entry(trigger_id)
        if entry is None:
            return None
        if entry.data.get(CONF_OPENING_TYPE) not in TYPES_ALERT_TRIGGER:
            # autoriser aussi si l'utilisateur a choisi une autre porte déjà créée
            pass
        return opening_contact_open(self.hass, entry)

    async def async_evaluate(self, *, initial: bool = False) -> None:
        """Recalcule si la lumière gateway doit être allumée."""
        if not self.enabled:
            if self._active:
                await self._async_set_light(False)
                self._active = False
                self._notify()
            return

        trigger_open = self._trigger_open()
        left_open = self._any_monitored_open()

        # Allumer seulement si porte déclencheur ouverte ET au moins une baie/fenêtre ouverte
        should_active = bool(trigger_open) and left_open

        # Éteindre si porte refermée OU plus aucune ouverture surveillée ouverte
        if trigger_open is False or not left_open:
            should_active = False

        if should_active == self._active:
            if not initial:
                self._notify()
            return

        self._active = should_active
        await self._async_set_light(should_active)
        self._notify()
        _LOGGER.info(
            "Alerte restée ouverte : %s (trigger_open=%s, left_open=%s)",
            "ON" if should_active else "OFF",
            trigger_open,
            left_open,
        )

    def _notify(self) -> None:
        self.hass.bus.async_fire(
            f"{DOMAIN}_alert_update",
            {"entry_id": self.entry.entry_id, "active": self._active},
        )

    async def _async_set_light(self, on: bool) -> None:
        light_id = self.data.get(CONF_ALERT_GATEWAY)
        if not light_id:
            return
        try:
            if on:
                await self.hass.services.async_call(
                    "light",
                    "turn_on",
                    {
                        "entity_id": light_id,
                        "rgb_color": _rgb(self.data.get(CONF_ALERT_COLOR)),
                        "brightness": _brightness(
                            self.data.get(CONF_ALERT_BRIGHTNESS, 180)
                        ),
                    },
                    blocking=False,
                )
            else:
                await self.hass.services.async_call(
                    "light",
                    "turn_off",
                    {"entity_id": light_id},
                    blocking=False,
                )
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Gateway %s : %s", light_id, err)

    async def async_set_enabled(self, enabled: bool) -> None:
        """Active / désactive via le switch (persiste dans les options)."""
        merged = {**self.entry.data, **self.entry.options}
        new_options = {
            CONF_ALERT_ENABLED: enabled,
            CONF_ALERT_MONITORED: merged.get(CONF_ALERT_MONITORED) or [],
            CONF_ALERT_TRIGGER: merged.get(CONF_ALERT_TRIGGER),
            CONF_ALERT_GATEWAY: merged.get(CONF_ALERT_GATEWAY),
            CONF_ALERT_COLOR: merged.get(CONF_ALERT_COLOR) or [255, 40, 0],
            CONF_ALERT_BRIGHTNESS: merged.get(CONF_ALERT_BRIGHTNESS, 180),
        }
        # Éteint tout de suite si on désactive (avant le reload options)
        if not enabled and self._active:
            self._active = False
            await self._async_set_light(False)
            self._notify()
        self.hass.config_entries.async_update_entry(self.entry, options=new_options)
