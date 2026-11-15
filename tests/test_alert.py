"""Tests de la logique alerte restée ouverte (sans Home Assistant installé)."""

from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "custom_components" / "ouvertures"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# Stubs HA minimaux avant import alert.py
ha = ModuleType("homeassistant")
ha_ce = ModuleType("homeassistant.config_entries")
ha_core = ModuleType("homeassistant.core")
ha_helpers = ModuleType("homeassistant.helpers")
ha_helpers_event = ModuleType("homeassistant.helpers.event")


class _ConfigEntry:  # noqa: D401
    pass


class _Event:
    pass


class _HomeAssistant:
    pass


def _callback(func):
    return func


ha_ce.ConfigEntry = _ConfigEntry
ha_core.Event = _Event
ha_core.HomeAssistant = _HomeAssistant
ha_core.callback = _callback
ha_helpers_event.async_track_state_change_event = MagicMock()

sys.modules["homeassistant"] = ha
sys.modules["homeassistant.config_entries"] = ha_ce
sys.modules["homeassistant.core"] = ha_core
sys.modules["homeassistant.helpers"] = ha_helpers
sys.modules["homeassistant.helpers.event"] = ha_helpers_event

pkg = ModuleType("ouvertures")
pkg.__path__ = [str(PKG)]  # type: ignore[attr-defined]
sys.modules["ouvertures"] = pkg
const = _load("ouvertures.const", PKG / "const.py")
helpers = _load("ouvertures.helpers", PKG / "helpers.py")
alert_mod = _load("ouvertures.alert", PKG / "alert.py")


class FakeState:
    def __init__(self, entity_id: str, state: str):
        self.entity_id = entity_id
        self.state = state
        self.attributes = {}


class FakeHass:
    def __init__(self):
        self.states = MagicMock()
        self.services = MagicMock()
        self.services.async_call = AsyncMock()
        self.bus = MagicMock()
        self.bus.async_fire = MagicMock()
        self.config_entries = MagicMock()
        self._entries: dict[str, MagicMock] = {}
        self.config_entries.async_get_entry = lambda eid: self._entries.get(eid)
        self.config_entries.async_entries = lambda domain=None: list(
            self._entries.values()
        )
        self.config_entries.async_update_entry = MagicMock()
        self.async_create_task = MagicMock()

    def add_entry(self, entry_id: str, data: dict):
        entry = MagicMock()
        entry.entry_id = entry_id
        entry.data = data
        entry.options = {}
        entry.title = data.get(const.CONF_NAME, entry_id)
        self._entries[entry_id] = entry
        return entry


def _opening(name, otype, contact, inverted=False):
    return {
        const.CONF_NAME: name,
        const.CONF_OPENING_TYPE: otype,
        const.CONF_CONTACT_ENTITY: contact,
        const.CONF_INVERTED: inverted,
    }


def _make_manager(hass: FakeHass):
    hass.add_entry(
        "baie1", _opening("Salon", const.TYPE_BAIE, "binary_sensor.baie")
    )
    hass.add_entry(
        "door1",
        _opening("Entrée", const.TYPE_PORTE_ENTREE, "binary_sensor.porte"),
    )
    alert_entry = hass.add_entry(
        "alert1",
        {
            const.CONF_NAME: const.ALERT_DEFAULT_NAME,
            const.CONF_OPENING_TYPE: const.TYPE_ALERTE_RESTEE,
            const.CONF_ALERT_ENABLED: True,
            const.CONF_ALERT_MONITORED: ["baie1"],
            const.CONF_ALERT_TRIGGER: "door1",
            const.CONF_ALERT_GATEWAY: "light.gateway",
            const.CONF_ALERT_COLOR: [255, 0, 0],
            const.CONF_ALERT_BRIGHTNESS: 200,
        },
    )
    return alert_mod.LeftOpenAlertManager(hass, alert_entry)


def test_constants_monitorable():
    assert const.TYPE_BAIE in const.TYPES_ALERT_MONITORABLE
    assert const.TYPE_FENETRE_SIMPLE in const.TYPES_ALERT_MONITORABLE
    assert const.TYPE_PORTE_FENETRE_3 in const.TYPES_ALERT_MONITORABLE
    assert const.TYPE_PORTE_ENTREE not in const.TYPES_ALERT_MONITORABLE
    assert const.TYPE_PORTE_ENTREE in const.TYPES_ALERT_TRIGGER
    assert const.ASSETS_VERSION.startswith("1.6.")


async def test_alert_turns_on_when_door_opens_with_window_open():
    hass = FakeHass()
    mgr = _make_manager(hass)

    def get_state(eid):
        mapping = {
            "binary_sensor.baie": FakeState(eid, "on"),
            "binary_sensor.porte": FakeState(eid, "on"),
        }
        return mapping.get(eid)

    hass.states.get.side_effect = get_state
    await mgr.async_evaluate()
    assert mgr.is_active is True
    args = hass.services.async_call.await_args
    assert args.args[0] == "light"
    assert args.args[1] == "turn_on"
    assert args.args[2]["rgb_color"] == [255, 0, 0]


async def test_alert_off_when_door_closes():
    hass = FakeHass()
    mgr = _make_manager(hass)
    mgr._active = True

    def get_state(eid):
        mapping = {
            "binary_sensor.baie": FakeState(eid, "on"),
            "binary_sensor.porte": FakeState(eid, "off"),
        }
        return mapping.get(eid)

    hass.states.get.side_effect = get_state
    await mgr.async_evaluate()
    assert mgr.is_active is False
    assert hass.services.async_call.await_args.args[1] == "turn_off"


async def test_alert_off_when_window_closes_while_door_open():
    hass = FakeHass()
    mgr = _make_manager(hass)
    mgr._active = True

    def get_state(eid):
        mapping = {
            "binary_sensor.baie": FakeState(eid, "off"),
            "binary_sensor.porte": FakeState(eid, "on"),
        }
        return mapping.get(eid)

    hass.states.get.side_effect = get_state
    await mgr.async_evaluate()
    assert mgr.is_active is False
    assert hass.services.async_call.await_args.args[1] == "turn_off"


async def test_alert_disabled_does_not_light():
    hass = FakeHass()
    mgr = _make_manager(hass)
    mgr.entry.data = {**mgr.entry.data, const.CONF_ALERT_ENABLED: False}

    hass.states.get.side_effect = lambda eid: FakeState(eid, "on")
    await mgr.async_evaluate()
    assert mgr.is_active is False
    hass.services.async_call.assert_not_awaited()


async def test_ignores_shutter_only_uses_contact():
    hass = FakeHass()
    hass.add_entry(
        "fen1",
        {
            const.CONF_NAME: "Chambre",
            const.CONF_OPENING_TYPE: const.TYPE_FENETRE_SIMPLE_VOLETS,
            const.CONF_CONTACT_ENTITY: "binary_sensor.fen",
            const.CONF_SHUTTER_ENTITY: "cover.volet",
            const.CONF_INVERTED: False,
        },
    )
    hass.add_entry(
        "door1",
        _opening("Entrée", const.TYPE_PORTE_ENTREE, "binary_sensor.porte"),
    )
    alert_entry = hass.add_entry(
        "alert1",
        {
            const.CONF_NAME: const.ALERT_DEFAULT_NAME,
            const.CONF_OPENING_TYPE: const.TYPE_ALERTE_RESTEE,
            const.CONF_ALERT_ENABLED: True,
            const.CONF_ALERT_MONITORED: ["fen1"],
            const.CONF_ALERT_TRIGGER: "door1",
            const.CONF_ALERT_GATEWAY: "light.gateway",
            const.CONF_ALERT_COLOR: [0, 255, 0],
            const.CONF_ALERT_BRIGHTNESS: 100,
        },
    )
    mgr = alert_mod.LeftOpenAlertManager(hass, alert_entry)

    def get_state(eid):
        mapping = {
            "binary_sensor.fen": FakeState(eid, "off"),
            "cover.volet": FakeState(eid, "open"),
            "binary_sensor.porte": FakeState(eid, "on"),
        }
        return mapping.get(eid)

    hass.states.get.side_effect = get_state
    await mgr.async_evaluate()
    assert mgr.is_active is False


def test_list_opening_options():
    hass = FakeHass()
    hass.add_entry("b1", _opening("Baie", const.TYPE_BAIE, "binary_sensor.a"))
    hass.add_entry(
        "d1", _opening("Porte", const.TYPE_PORTE_ENTREE, "binary_sensor.b")
    )
    opts = alert_mod.list_opening_options(
        hass, allowed_types=const.TYPES_ALERT_MONITORABLE
    )
    assert len(opts) == 1
    assert opts[0]["value"] == "b1"
    assert "Baie" in opts[0]["label"]


if __name__ == "__main__":
    test_constants_monitorable()
    asyncio.run(test_alert_turns_on_when_door_opens_with_window_open())
    asyncio.run(test_alert_off_when_door_closes())
    asyncio.run(test_alert_off_when_window_closes_while_door_open())
    asyncio.run(test_alert_disabled_does_not_light())
    asyncio.run(test_ignores_shutter_only_uses_contact())
    test_list_opening_options()
    print("OK — tests alerte passent")
