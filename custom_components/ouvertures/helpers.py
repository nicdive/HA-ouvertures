"""Helpers pour déterminer les états d'ouverture."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .const import (
    CLOSED_STATES,
    OPEN_STATES,
    STATE_FERME,
    STATE_FERMEE_VOLETS_FERMES,
    STATE_FERMEE_VOLETS_OUVERTS,
    STATE_INCONNU,
    STATE_OUVERT,
    STATE_OUVERTE_VOLETS_FERMES,
    STATE_OUVERTE_VOLETS_OUVERTS,
    TYPE_BAIE,
    TYPE_GARAGE,
    TYPE_PISCINE,
    TYPE_PORTAIL,
    TYPE_PORTE,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, State


def _position_open(state: Any) -> bool | None:
    try:
        pos = state.attributes.get("current_position")
        if pos is None:
            return None
        return float(pos) > 5
    except (TypeError, ValueError, AttributeError):
        return None


def is_entity_open(state: Any, inverted: bool = False) -> bool | None:
    """Retourne True/False/None selon l'état de l'entité."""
    if state is None or state.state is None:
        return None

    value = str(state.state).lower().strip()
    if value in OPEN_STATES:
        result = True
    elif value in CLOSED_STATES:
        result = False
    else:
        # unknown/unavailable ou état libre → tenter la position cover
        result = _position_open(state)
        if result is None:
            return None
    return (not result) if inverted else result


def combined_state(
    opening_type: str,
    contact_open: bool | None,
    shutter_open: bool | None = None,
) -> str:
    """Calcule l'état combiné affiché / image."""
    if contact_open is None:
        return STATE_INCONNU

    if opening_type == TYPE_BAIE:
        if shutter_open is None:
            return STATE_OUVERT if contact_open else STATE_FERME
        if contact_open and shutter_open:
            return STATE_OUVERTE_VOLETS_OUVERTS
        if contact_open and not shutter_open:
            return STATE_OUVERTE_VOLETS_FERMES
        if not contact_open and shutter_open:
            return STATE_FERMEE_VOLETS_OUVERTS
        return STATE_FERMEE_VOLETS_FERMES

    return STATE_OUVERT if contact_open else STATE_FERME


def image_for_state(opening_type: str, state: str) -> str:
    """Nom de fichier image relatif."""
    mapping: dict[str, dict[str, str]] = {
        TYPE_BAIE: {
            STATE_FERMEE_VOLETS_OUVERTS: "baie_fermee_volets_ouverts.svg",
            STATE_OUVERTE_VOLETS_OUVERTS: "baie_ouverte_volets_ouverts.svg",
            STATE_FERMEE_VOLETS_FERMES: "baie_fermee_volets_fermes.svg",
            STATE_OUVERTE_VOLETS_FERMES: "baie_ouverte_volets_fermes.svg",
            STATE_FERME: "baie_fermee_volets_fermes.svg",
            STATE_OUVERT: "baie_ouverte_volets_ouverts.svg",
        },
        TYPE_PORTE: {
            STATE_FERME: "porte_fermee.svg",
            STATE_OUVERT: "porte_ouverte.svg",
        },
        TYPE_PORTAIL: {
            STATE_FERME: "portail_ferme.svg",
            STATE_OUVERT: "portail_ouvert.svg",
        },
        TYPE_GARAGE: {
            STATE_FERME: "garage_ferme.svg",
            STATE_OUVERT: "garage_ouvert.svg",
        },
        TYPE_PISCINE: {
            STATE_FERME: "piscine_fermee.svg",
            STATE_OUVERT: "piscine_ouverte.svg",
        },
    }
    type_map = mapping.get(opening_type, {})
    return type_map.get(state, type_map.get(STATE_FERME, "porte_fermee.svg"))


def human_label(opening_type: str, state: str) -> str:
    """Libellé français de l'état."""
    labels = {
        STATE_FERMEE_VOLETS_OUVERTS: "Baie fermée · Volets ouverts",
        STATE_OUVERTE_VOLETS_OUVERTS: "Baie ouverte · Volets ouverts",
        STATE_FERMEE_VOLETS_FERMES: "Baie fermée · Volets fermés",
        STATE_OUVERTE_VOLETS_FERMES: "Baie ouverte · Volets fermés",
        STATE_FERME: {
            TYPE_PORTE: "Porte fermée",
            TYPE_PORTAIL: "Portail fermé",
            TYPE_GARAGE: "Garage fermé",
            TYPE_PISCINE: "Volet fermé",
            TYPE_BAIE: "Baie fermée",
        }.get(opening_type, "Fermé"),
        STATE_OUVERT: {
            TYPE_PORTE: "Porte ouverte",
            TYPE_PORTAIL: "Portail ouvert",
            TYPE_GARAGE: "Garage ouvert",
            TYPE_PISCINE: "Volet ouvert",
            TYPE_BAIE: "Baie ouverte",
        }.get(opening_type, "Ouvert"),
        STATE_INCONNU: "État inconnu",
    }
    return labels.get(state, state)


def is_alert(opening_type: str, state: str) -> bool:
    """True si l'état doit être signalé (ouverture)."""
    return state in (
        STATE_OUVERT,
        STATE_OUVERTE_VOLETS_OUVERTS,
        STATE_OUVERTE_VOLETS_FERMES,
    )


def resolve_opening(
    hass: Any,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Calcule l'état courant d'une ouverture à partir de sa config."""
    from .const import (
        CONF_CLOSE_ENTITY,
        CONF_CONTACT_ENTITY,
        CONF_IMPULSE_ENTITY,
        CONF_INVERTED,
        CONF_OPEN_ENTITY,
        CONF_OPENING_TYPE,
        CONF_SHUTTER_ENTITY,
        STATIC_URL_PATH,
    )

    opening_type = data[CONF_OPENING_TYPE]
    inverted = bool(data.get(CONF_INVERTED, False))
    contact_id = data.get(CONF_CONTACT_ENTITY)
    shutter_id = data.get(CONF_SHUTTER_ENTITY)

    contact_state = hass.states.get(contact_id) if contact_id else None
    shutter_state = hass.states.get(shutter_id) if shutter_id else None

    contact_open = is_entity_open(contact_state, inverted)
    shutter_open = (
        is_entity_open(shutter_state, False) if shutter_id else None
    )

    state = combined_state(opening_type, contact_open, shutter_open)
    image = image_for_state(opening_type, state)

    return {
        "state": state,
        "label": human_label(opening_type, state),
        "is_open": bool(contact_open) if contact_open is not None else False,
        "is_alert": is_alert(opening_type, state),
        "shutter_open": shutter_open,
        "image": f"{STATIC_URL_PATH}/img/{image}",
        "image_file": image,
        "contact_entity": contact_id,
        "shutter_entity": shutter_id,
        "open_entity": data.get(CONF_OPEN_ENTITY),
        "close_entity": data.get(CONF_CLOSE_ENTITY),
        "impulse_entity": data.get(CONF_IMPULSE_ENTITY),
        "opening_type": opening_type,
    }
