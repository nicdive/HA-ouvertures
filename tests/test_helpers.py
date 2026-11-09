"""Tests unitaires des helpers d'état (sans Home Assistant installé)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "custom_components" / "ouvertures"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# Charge const + helpers sans exécuter ouvertures/__init__.py
pkg = ModuleType("ouvertures")
pkg.__path__ = [str(PKG)]  # type: ignore[attr-defined]
sys.modules["ouvertures"] = pkg
const = _load("ouvertures.const", PKG / "const.py")
helpers = _load("ouvertures.helpers", PKG / "helpers.py")


def _state(value: str, **attrs):
    return SimpleNamespace(state=value, attributes=attrs)


def test_is_entity_open_binary():
    assert helpers.is_entity_open(_state("on")) is True
    assert helpers.is_entity_open(_state("off")) is False
    assert helpers.is_entity_open(_state("on"), inverted=True) is False
    assert helpers.is_entity_open(_state("unknown")) is None


def test_is_entity_open_cover_position():
    assert helpers.is_entity_open(_state("unknown", current_position=80)) is True
    assert helpers.is_entity_open(_state("unknown", current_position=0)) is False


def test_baie_combined_states():
    assert (
        helpers.combined_state(const.TYPE_BAIE, False, True)
        == const.STATE_FERMEE_VOLETS_OUVERTS
    )
    assert (
        helpers.combined_state(const.TYPE_BAIE, True, True)
        == const.STATE_OUVERTE_VOLETS_OUVERTS
    )
    assert (
        helpers.combined_state(const.TYPE_BAIE, False, False)
        == const.STATE_FERMEE_VOLETS_FERMES
    )
    assert (
        helpers.combined_state(const.TYPE_BAIE, True, False)
        == const.STATE_OUVERTE_VOLETS_FERMES
    )


def test_porte_states():
    assert helpers.combined_state(const.TYPE_PORTE, False) == const.STATE_FERME
    assert helpers.combined_state(const.TYPE_PORTE, True) == const.STATE_OUVERT
    assert helpers.is_alert(const.TYPE_PORTE, const.STATE_OUVERT) is True
    assert helpers.is_alert(const.TYPE_PORTE, const.STATE_FERME) is False


def test_images_and_labels():
    img = helpers.image_for_state(
        const.TYPE_BAIE, const.STATE_OUVERTE_VOLETS_FERMES
    )
    assert img == "baie_ouverte_volets_fermes.svg"
    label = helpers.human_label(const.TYPE_BAIE, const.STATE_OUVERTE_VOLETS_FERMES)
    assert "ouverte" in label.lower()


if __name__ == "__main__":
    test_is_entity_open_binary()
    test_is_entity_open_cover_position()
    test_baie_combined_states()
    test_porte_states()
    test_images_and_labels()
    print("OK — tous les tests helpers passent")
