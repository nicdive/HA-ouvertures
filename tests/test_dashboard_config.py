"""Tests de construction de la config dashboard (sans Home Assistant)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "custom_components" / "ouvertures"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


pkg = ModuleType("ouvertures")
pkg.__path__ = [str(PKG)]  # type: ignore[attr-defined]
sys.modules["ouvertures"] = pkg
const = _load("ouvertures.const", PKG / "const.py")

# Stub homeassistant modules used at import-time by dashboard.py
for name in (
    "homeassistant",
    "homeassistant.config_entries",
    "homeassistant.const",
    "homeassistant.core",
    "homeassistant.helpers",
    "homeassistant.helpers.entity_registry",
):
    if name not in sys.modules:
        sys.modules[name] = ModuleType(name)

ha_core = sys.modules["homeassistant.core"]
ha_core.HomeAssistant = object  # type: ignore[attr-defined]
ha_core.Event = object  # type: ignore[attr-defined]
ha_core.callback = lambda f: f  # type: ignore[attr-defined]

ha_const = sys.modules["homeassistant.const"]
ha_const.EVENT_HOMEASSISTANT_STARTED = "homeassistant_started"  # type: ignore[attr-defined]

ha_ce = sys.modules["homeassistant.config_entries"]
ha_ce.ConfigEntry = object  # type: ignore[attr-defined]

dashboard = _load("ouvertures.dashboard", PKG / "dashboard.py")


def test_build_config_groups_types():
    grouped = {
        const.TYPE_BAIE: [
            {"entity_id": "sensor.baie_salon_etat", "name": "Baie salon"}
        ],
        const.TYPE_PORTE: [],
        const.TYPE_PORTAIL: [
            {"entity_id": "sensor.portail_etat", "name": "Portail"}
        ],
        const.TYPE_GARAGE: [],
        const.TYPE_PISCINE: [],
    }
    cfg = dashboard._build_config(grouped)
    assert "views" in cfg
    assert len(cfg["views"]) == 2
    # Section baie + portail
    sections = cfg["views"][0]["sections"]
    assert len(sections) == 2
    overview = cfg["views"][1]["sections"][0]["cards"]
    card = next(c for c in overview if c.get("type") == "custom:ouvertures-card")
    assert "sensor.baie_salon_etat" in card["entities"]
    assert "sensor.portail_etat" in card["entities"]


def test_build_config_empty():
    grouped = {t: [] for t in dashboard._TYPE_ORDER}
    cfg = dashboard._build_config(grouped)
    assert "markdown" in str(cfg).lower()


if __name__ == "__main__":
    test_build_config_groups_types()
    test_build_config_empty()
    print("OK — tests dashboard config")
