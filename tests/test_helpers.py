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


def test_binary_zero_one_default_and_inverted():
    """Par défaut 1=ouvert / 0=fermé ; avec inverted : 0=ouvert / 1=fermé."""
    assert helpers.is_entity_open(_state("1")) is True
    assert helpers.is_entity_open(_state("0")) is False
    # Cas utilisateur : 0 = open, 1 = closed
    assert helpers.is_entity_open(_state("0"), inverted=True) is True
    assert helpers.is_entity_open(_state("1"), inverted=True) is False
    assert helpers.is_entity_open(_state("off"), inverted=True) is True
    assert helpers.is_entity_open(_state("on"), inverted=True) is False
    # Valeurs numériques brutes
    assert helpers.is_entity_open(_state(0), inverted=True) is True
    assert helpers.is_entity_open(_state(1), inverted=True) is False


def test_numeric_sensor_zero_dot_zero():
    """Sensors xPL / remote HA : état '0.0' / '1.0' (pas on/off)."""
    # Sans invert : 0.0 = fermé, 1.0 = ouvert
    assert helpers.is_entity_open(_state("0.0")) is False
    assert helpers.is_entity_open(_state("1.0")) is True
    # Volet piscine utilisateur : 0.0 = ouvert → inverted
    assert helpers.is_entity_open(_state("0.0"), inverted=True) is True
    assert helpers.is_entity_open(_state("1.0"), inverted=True) is False
    assert helpers.is_entity_open(_state(0.0), inverted=True) is True
    assert helpers.is_entity_open(_state(1.0), inverted=True) is False
    # Combiné piscine
    assert (
        helpers.combined_state(
            const.TYPE_PISCINE,
            helpers.is_entity_open(_state("0.0"), inverted=True),
        )
        == const.STATE_OUVERT
    )


def test_is_entity_open_cover_position():
    assert helpers.is_entity_open(_state("unknown", current_position=80)) is True
    assert helpers.is_entity_open(_state("unknown", current_position=0)) is False


def test_cover_entity_prefers_position():
    """Volet roulant : current_position prime sur l'état textuel."""
    open_cover = SimpleNamespace(
        state="open", entity_id="cover.volet_salon", attributes={"current_position": 100}
    )
    closed_cover = SimpleNamespace(
        state="closed", entity_id="cover.volet_salon", attributes={"current_position": 0}
    )
    mid = SimpleNamespace(
        state="open", entity_id="cover.volet_salon", attributes={"current_position": 3}
    )
    assert helpers.is_entity_open(open_cover) is True
    assert helpers.is_entity_open(closed_cover) is False
    assert helpers.is_entity_open(mid) is False


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


def test_fenetre_simple_sans_volets():
    assert (
        helpers.combined_state(const.TYPE_FENETRE_SIMPLE, False)
        == const.STATE_FERME
    )
    assert (
        helpers.combined_state(const.TYPE_FENETRE_SIMPLE, True)
        == const.STATE_OUVERT
    )
    assert (
        helpers.image_for_state(const.TYPE_FENETRE_SIMPLE, const.STATE_OUVERT)
        == "fenetre_simple_ouverte.svg"
    )
    assert "Fenêtre" in helpers.human_label(
        const.TYPE_FENETRE_SIMPLE, const.STATE_OUVERT
    )


def test_fenetre_double_avec_volets():
    assert (
        helpers.combined_state(const.TYPE_FENETRE_DOUBLE_VOLETS, False, True)
        == const.STATE_FERMEE_VOLETS_OUVERTS
    )
    img = helpers.image_for_state(
        const.TYPE_FENETRE_DOUBLE_VOLETS, const.STATE_FERMEE_VOLETS_OUVERTS
    )
    assert img == "fenetre_double_fermee_volets_ouverts.svg"
    label = helpers.human_label(
        const.TYPE_FENETRE_DOUBLE_VOLETS, const.STATE_FERMEE_VOLETS_OUVERTS
    )
    assert label.startswith("Fenêtre")
    assert "Volets ouverts" in label


def test_opening_types_include_fenetres():
    for key in (
        const.TYPE_FENETRE_SIMPLE,
        const.TYPE_FENETRE_SIMPLE_VOLETS,
        const.TYPE_FENETRE_DOUBLE,
        const.TYPE_FENETRE_DOUBLE_VOLETS,
    ):
        assert key in const.OPENING_TYPES
    assert const.TYPE_FENETRE_SIMPLE_VOLETS in const.TYPES_WITH_SHUTTERS
    assert const.TYPE_FENETRE_SIMPLE not in const.TYPES_WITH_SHUTTERS


def test_porte_fenetre_3_battants():
    assert const.TYPE_PORTE_FENETRE_3 in const.OPENING_TYPES
    assert const.TYPE_PORTE_FENETRE_3 in const.TYPES_WITH_SHUTTERS
    assert const.OPENING_TYPES[const.TYPE_PORTE_FENETRE_3].get("shutter_cover_only") is True
    assert (
        helpers.combined_state(const.TYPE_PORTE_FENETRE_3, True, False)
        == const.STATE_OUVERTE_VOLETS_FERMES
    )
    img = helpers.image_for_state(
        const.TYPE_PORTE_FENETRE_3, const.STATE_FERMEE_VOLETS_OUVERTS
    )
    assert img == "porte_fenetre_3_fermee_volet_ouvert.svg"
    label = helpers.human_label(
        const.TYPE_PORTE_FENETRE_3, const.STATE_FERMEE_VOLETS_OUVERTS
    )
    assert label.startswith("Porte-fenêtre")
    assert "Volet ouvert" in label


def test_porte_entree_and_realistic_images():
    assert const.TYPE_PORTE_ENTREE in const.OPENING_TYPES
    assert const.OPENING_TYPES[const.TYPE_PORTE]["label"] == "Porte garage simple"
    assert const.OPENING_TYPES[const.TYPE_PORTE_ENTREE]["label"] == "Porte d'entrée"
    assert (
        helpers.image_for_state(const.TYPE_PORTE_ENTREE, const.STATE_FERME)
        == "porte_entree_fermee.svg"
    )
    assert (
        helpers.image_for_state(const.TYPE_PORTE_ENTREE, const.STATE_OUVERT)
        == "porte_entree_ouverte.svg"
    )
    assert (
        helpers.image_for_state(const.TYPE_PORTE, const.STATE_FERME)
        == "porte_simple_fermee.svg"
    )
    assert (
        helpers.image_for_state(const.TYPE_PORTAIL, const.STATE_FERME)
        == "portail_coulissant_ferme.svg"
    )
    assert (
        helpers.image_for_state(const.TYPE_GARAGE, const.STATE_FERME)
        == "garage_sectionnelle_ferme.svg"
    )
    assert helpers.human_label(const.TYPE_PORTE_ENTREE, const.STATE_OUVERT) == "Porte ouverte"
    assert helpers.is_alert(const.TYPE_PORTE_ENTREE, const.STATE_OUVERT) is True


if __name__ == "__main__":
    test_is_entity_open_binary()
    test_binary_zero_one_default_and_inverted()
    test_numeric_sensor_zero_dot_zero()
    test_is_entity_open_cover_position()
    test_cover_entity_prefers_position()
    test_baie_combined_states()
    test_porte_states()
    test_images_and_labels()
    test_fenetre_simple_sans_volets()
    test_fenetre_double_avec_volets()
    test_opening_types_include_fenetres()
    test_porte_fenetre_3_battants()
    test_porte_entree_and_realistic_images()
    print("OK — tous les tests helpers passent")
