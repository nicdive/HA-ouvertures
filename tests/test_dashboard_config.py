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


def test_dashboard_groups_by_room_one_card_each():
    items = [
        {
            "entity_id": "sensor.baie_salon_etat",
            "name": "Baie Est",
            "opening_type": const.TYPE_BAIE,
            "area": "Salon",
        },
        {
            "entity_id": "sensor.baie_cuisine_etat",
            "name": "Baie Cuisine",
            "opening_type": const.TYPE_BAIE,
            "area": "Cuisine",
        },
        {
            "entity_id": "sensor.portail_etat",
            "name": "Portail",
            "opening_type": const.TYPE_PORTAIL,
            "area": "",
        },
    ]
    cfg = dashboard._build_config(items)
    view = cfg["views"][0]
    assert view["title"] == "Par pièce"
    sections = view["sections"]
    assert len(sections) == 3  # Cuisine, Salon, Sans pièce

    headings = [
        c["heading"]
        for s in sections
        for c in s["cards"]
        if c.get("type") == "heading"
    ]
    assert headings == ["Cuisine", "Salon", "Sans pièce"]

    # Une carte par ouverture (pas une grille d'entities)
    opening_cards = [
        c
        for s in sections
        for c in s["cards"]
        if c.get("type") == "custom:ouvertures-card"
    ]
    assert len(opening_cards) == 3
    assert all("entity" in c and "entities" not in c for c in opening_cards)


def test_build_config_empty():
    cfg = dashboard._build_config([])
    assert "markdown" in str(cfg).lower()


if __name__ == "__main__":
    test_dashboard_groups_by_room_one_card_each()
    test_build_config_empty()
    print("OK — tests dashboard config")
