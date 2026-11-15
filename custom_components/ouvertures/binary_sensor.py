"""Capteur binaire ouvert / fermé + alerte restée ouverte."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .alert import DATA_ALERT_MANAGER, LeftOpenAlertManager
from .const import (
    ALERT_DEFAULT_NAME,
    CONF_NAME,
    CONF_OPENING_TYPE,
    DOMAIN,
    OPENING_TYPES,
    TYPE_ALERTE_RESTEE,
    TYPE_BAIE,
    TYPE_FENETRE_DOUBLE,
    TYPE_FENETRE_DOUBLE_VOLETS,
    TYPE_FENETRE_SIMPLE,
    TYPE_FENETRE_SIMPLE_VOLETS,
    TYPE_GARAGE,
    TYPE_PORTAIL,
    TYPE_PORTE_FENETRE_3,
)
from .entity import OuvertureEntity

_WINDOW_TYPES = frozenset(
    {
        TYPE_FENETRE_SIMPLE,
        TYPE_FENETRE_SIMPLE_VOLETS,
        TYPE_FENETRE_DOUBLE,
        TYPE_FENETRE_DOUBLE_VOLETS,
    }
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    if entry.data.get(CONF_OPENING_TYPE) == TYPE_ALERTE_RESTEE:
        async_add_entities([AlertActiveBinarySensor(hass, entry)])
        return
    async_add_entities([OuvertureOpenBinarySensor(hass, entry)])


class OuvertureOpenBinarySensor(OuvertureEntity, BinarySensorEntity):
    """Indique si l'ouverture est ouverte."""

    _attr_name = "Ouvert"
    _attr_translation_key = "ouvert"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry)
        self._attr_unique_id = f"{entry.entry_id}_ouvert"
        opening_type = self.entry_data[CONF_OPENING_TYPE]
        if opening_type == TYPE_GARAGE:
            self._attr_device_class = BinarySensorDeviceClass.GARAGE_DOOR
        elif opening_type in _WINDOW_TYPES:
            self._attr_device_class = BinarySensorDeviceClass.WINDOW
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
            if opening_type in (TYPE_BAIE, TYPE_PORTE_FENETRE_3):
                return "mdi:door-sliding-open"
            if opening_type in _WINDOW_TYPES:
                return "mdi:window-open-variant"
            return "mdi:door-open"
        return base


class AlertActiveBinarySensor(BinarySensorEntity):
    """True quand la gateway affiche l'alerte (porte ouverte + baie/fenêtre ouverte)."""

    _attr_has_entity_name = True
    _attr_name = "Alerte active"
    _attr_translation_key = "alerte_active"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:bell-alert"
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_active"
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
        return bool(mgr and mgr.is_active)

    @property
    def extra_state_attributes(self) -> dict:
        mgr = self._manager()
        return {
            "ouvertures_restees_ouvertes": mgr.open_monitored_names() if mgr else [],
        }

    async def async_added_to_hass(self) -> None:
        @callback
        def _on_update(_event: Event) -> None:
            self.async_write_ha_state()

        self.async_on_remove(
            self.hass.bus.async_listen(f"{DOMAIN}_alert_update", _on_update)
        )
