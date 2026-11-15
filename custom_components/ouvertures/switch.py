"""Switch pour activer / désactiver l'alerte restée ouverte."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .alert import DATA_ALERT_MANAGER, LeftOpenAlertManager
from .const import (
    ALERT_DEFAULT_NAME,
    CONF_ALERT_ENABLED,
    CONF_NAME,
    CONF_OPENING_TYPE,
    DOMAIN,
    TYPE_ALERTE_RESTEE,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    if entry.data.get(CONF_OPENING_TYPE) != TYPE_ALERTE_RESTEE:
        return
    async_add_entities([AlertEnabledSwitch(hass, entry)])


class AlertEnabledSwitch(SwitchEntity):
    """Active ou coupe l'alerte gateway."""

    _attr_has_entity_name = True
    _attr_name = "Activée"
    _attr_translation_key = "alerte_activee"
    _attr_icon = "mdi:bell-badge"
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_enabled"
        name = entry.data.get(CONF_NAME) or ALERT_DEFAULT_NAME
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=name,
            manufacturer="Ouvertures",
            model="Alerte restée ouverte",
        )

    def _manager(self) -> LeftOpenAlertManager | None:
        store = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id, {})
        return store.get(DATA_ALERT_MANAGER)

    @property
    def is_on(self) -> bool:
        mgr = self._manager()
        if mgr is not None:
            return mgr.enabled
        data = {**self._entry.data, **self._entry.options}
        return bool(data.get(CONF_ALERT_ENABLED, True))

    async def async_turn_on(self, **kwargs) -> None:
        mgr = self._manager()
        if mgr is not None:
            await mgr.async_set_enabled(True)
        else:
            self.hass.config_entries.async_update_entry(
                self._entry,
                options={**self._entry.options, CONF_ALERT_ENABLED: True},
            )
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        mgr = self._manager()
        if mgr is not None:
            await mgr.async_set_enabled(False)
        else:
            self.hass.config_entries.async_update_entry(
                self._entry,
                options={**self._entry.options, CONF_ALERT_ENABLED: False},
            )
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        @callback
        def _on_update(_event: Event) -> None:
            self.async_write_ha_state()

        self.async_on_remove(
            self.hass.bus.async_listen(f"{DOMAIN}_alert_update", _on_update)
        )
