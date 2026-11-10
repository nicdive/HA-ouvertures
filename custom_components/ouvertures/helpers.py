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
    TYPE_FENETRE_DOUBLE,
    TYPE_FENETRE_DOUBLE_VOLETS,
    TYPE_FENETRE_SIMPLE,
    TYPE_FENETRE_SIMPLE_VOLETS,
    TYPE_GARAGE,
    TYPE_PISCINE,
    TYPE_PORTAIL,
    TYPE_PORTE,
    TYPE_PORTE_FENETRE_3,
    TYPES_WITH_SHUTTERS,
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


def _normalize_state_value(raw: Any) -> str:
    """Normalise on/off, 0/1, true/false (str ou nombre)."""
    if raw is None:
        return ""
    if isinstance(raw, bool):
        return "on" if raw else "off"
    if isinstance(raw, (int, float)):
        # 1 / 1.0 → "1" ; 0 / 0.0 → "0"
        return "1" if float(raw) != 0 else "0"
    value = str(raw).lower().strip()
    # "1.0", "0.0" venant de certains sensors
    try:
        as_float = float(value)
        if as_float in (0.0, 1.0):
            return "1" if as_float == 1.0 else "0"
    except ValueError:
        pass
    return value


def is_entity_open(state: Any, inverted: bool = False) -> bool | None:
    """Retourne True/False/None selon l'état de l'entité.

    Convention par défaut (comme Home Assistant) :
    - ouvert : ``on`` / ``open`` / ``1``
    - fermé : ``off`` / ``closed`` / ``0``

    Si le capteur est inversé (0 = ouvert, 1 = fermé), passer
    ``inverted=True`` (case à cocher dans la config).

    Pour un *cover* (volet roulant), ``current_position`` prime
    (0 = fermé, 100 = ouvert).
    """
    if state is None or state.state is None:
        return None

    entity_id = str(getattr(state, "entity_id", "") or "")
    if entity_id.startswith("cover."):
        pos = _position_open(state)
        if pos is not None:
            return (not pos) if inverted else pos

    value = _normalize_state_value(state.state)
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

    if opening_type in TYPES_WITH_SHUTTERS:
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
        TYPE_FENETRE_SIMPLE: {
            STATE_FERME: "fenetre_simple_fermee.svg",
            STATE_OUVERT: "fenetre_simple_ouverte.svg",
        },
        TYPE_FENETRE_SIMPLE_VOLETS: {
            STATE_FERMEE_VOLETS_OUVERTS: "fenetre_simple_fermee_volets_ouverts.svg",
            STATE_OUVERTE_VOLETS_OUVERTS: "fenetre_simple_ouverte_volets_ouverts.svg",
            STATE_FERMEE_VOLETS_FERMES: "fenetre_simple_fermee_volets_fermes.svg",
            STATE_OUVERTE_VOLETS_FERMES: "fenetre_simple_ouverte_volets_fermes.svg",
            STATE_FERME: "fenetre_simple_fermee_volets_fermes.svg",
            STATE_OUVERT: "fenetre_simple_ouverte_volets_ouverts.svg",
        },
        TYPE_FENETRE_DOUBLE: {
            STATE_FERME: "fenetre_double_fermee.svg",
            STATE_OUVERT: "fenetre_double_ouverte.svg",
        },
        TYPE_FENETRE_DOUBLE_VOLETS: {
            STATE_FERMEE_VOLETS_OUVERTS: "fenetre_double_fermee_volets_ouverts.svg",
            STATE_OUVERTE_VOLETS_OUVERTS: "fenetre_double_ouverte_volets_ouverts.svg",
            STATE_FERMEE_VOLETS_FERMES: "fenetre_double_fermee_volets_fermes.svg",
            STATE_OUVERTE_VOLETS_FERMES: "fenetre_double_ouverte_volets_fermes.svg",
            STATE_FERME: "fenetre_double_fermee_volets_fermes.svg",
            STATE_OUVERT: "fenetre_double_ouverte_volets_ouverts.svg",
        },
        TYPE_PORTE_FENETRE_3: {
            STATE_FERMEE_VOLETS_OUVERTS: "porte_fenetre_3_fermee_volet_ouvert.svg",
            STATE_OUVERTE_VOLETS_OUVERTS: "porte_fenetre_3_ouverte_volet_ouvert.svg",
            STATE_FERMEE_VOLETS_FERMES: "porte_fenetre_3_fermee_volet_ferme.svg",
            STATE_OUVERTE_VOLETS_FERMES: "porte_fenetre_3_ouverte_volet_ferme.svg",
            STATE_FERME: "porte_fenetre_3_fermee_volet_ferme.svg",
            STATE_OUVERT: "porte_fenetre_3_ouverte_volet_ouvert.svg",
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


def _noun(opening_type: str) -> str:
    if opening_type == TYPE_BAIE:
        return "Baie"
    if opening_type == TYPE_PORTE_FENETRE_3:
        return "Porte-fenêtre"
    if opening_type in (
        TYPE_FENETRE_SIMPLE,
        TYPE_FENETRE_SIMPLE_VOLETS,
        TYPE_FENETRE_DOUBLE,
        TYPE_FENETRE_DOUBLE_VOLETS,
    ):
        return "Fenêtre"
    if opening_type == TYPE_PORTE:
        return "Porte"
    if opening_type == TYPE_PORTAIL:
        return "Portail"
    if opening_type == TYPE_GARAGE:
        return "Garage"
    if opening_type == TYPE_PISCINE:
        return "Volet"
    return "Ouverture"


def human_label(opening_type: str, state: str) -> str:
    """Libellé français de l'état."""
    noun = _noun(opening_type)
    if opening_type == TYPE_PORTE_FENETRE_3:
        shutter_open = "Volet ouvert"
        shutter_closed = "Volet fermé"
    else:
        shutter_open = "Volets ouverts"
        shutter_closed = "Volets fermés"
    if state == STATE_FERMEE_VOLETS_OUVERTS:
        return f"{noun} fermée · {shutter_open}"
    if state == STATE_OUVERTE_VOLETS_OUVERTS:
        return f"{noun} ouverte · {shutter_open}"
    if state == STATE_FERMEE_VOLETS_FERMES:
        return f"{noun} fermée · {shutter_closed}"
    if state == STATE_OUVERTE_VOLETS_FERMES:
        return f"{noun} ouverte · {shutter_closed}"
    if state == STATE_FERME:
        if opening_type == TYPE_PORTAIL:
            return "Portail fermé"
        if opening_type == TYPE_GARAGE:
            return "Garage fermé"
        if opening_type == TYPE_PISCINE:
            return "Volet fermé"
        if opening_type == TYPE_PORTE:
            return "Porte fermée"
        return f"{noun} fermée"
    if state == STATE_OUVERT:
        if opening_type == TYPE_PORTAIL:
            return "Portail ouvert"
        if opening_type == TYPE_GARAGE:
            return "Garage ouvert"
        if opening_type == TYPE_PISCINE:
            return "Volet ouvert"
        if opening_type == TYPE_PORTE:
            return "Porte ouverte"
        return f"{noun} ouverte"
    if state == STATE_INCONNU:
        return "État inconnu"
    return state


def is_alert(opening_type: str, state: str) -> bool:
    """True si l'état doit être signalé (ouverture)."""
    return state in (
        STATE_OUVERT,
        STATE_OUVERTE_VOLETS_OUVERTS,
        STATE_OUVERTE_VOLETS_FERMES,
    )


def resolve_area_name(
    hass: Any,
    *,
    device_id: str | None = None,
    entity_ids: list[str] | None = None,
) -> str | None:
    """Retrouve le nom de pièce (area) HA pour un device / des entités liées."""
    try:
        from homeassistant.helpers import (
            area_registry as ar,
            device_registry as dr,
            entity_registry as er,
        )
    except Exception:  # noqa: BLE001
        return None

    area_reg = ar.async_get(hass)
    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)

    area_id: str | None = None

    if device_id:
        device = dev_reg.async_get(device_id)
        if device and device.area_id:
            area_id = device.area_id

    if area_id is None and entity_ids:
        for eid in entity_ids:
            if not eid:
                continue
            entry = ent_reg.async_get(eid)
            if not entry:
                continue
            if entry.area_id:
                area_id = entry.area_id
                break
            if entry.device_id:
                device = dev_reg.async_get(entry.device_id)
                if device and device.area_id:
                    area_id = device.area_id
                    break

    if not area_id:
        return None
    area = area_reg.async_get_area(area_id)
    return area.name if area else None


def resolve_opening(
    hass: Any,
    data: dict[str, Any],
    *,
    device_id: str | None = None,
) -> dict[str, Any]:
    """Calcule l'état courant d'une ouverture à partir de sa config."""
    from .const import (
        CONF_CLOSE_ENTITY,
        CONF_CONTACT_ENTITY,
        CONF_IMPULSE_ENTITY,
        CONF_INVERTED,
        CONF_NAME,
        CONF_OPEN_ENTITY,
        CONF_OPENING_TYPE,
        CONF_SHUTTER_ENTITY,
        STATIC_URL_PATH,
    )

    opening_type = data[CONF_OPENING_TYPE]
    inverted = bool(data.get(CONF_INVERTED, False))
    contact_id = data.get(CONF_CONTACT_ENTITY)
    shutter_id = data.get(CONF_SHUTTER_ENTITY)
    name = data.get(CONF_NAME) or ""

    contact_state = hass.states.get(contact_id) if contact_id else None
    shutter_state = hass.states.get(shutter_id) if shutter_id else None

    contact_open = is_entity_open(contact_state, inverted)
    shutter_open = (
        is_entity_open(shutter_state, False) if shutter_id else None
    )

    state = combined_state(opening_type, contact_open, shutter_open)
    image = image_for_state(opening_type, state)
    area = resolve_area_name(
        hass,
        device_id=device_id,
        entity_ids=[
            contact_id,
            shutter_id,
            data.get(CONF_OPEN_ENTITY),
            data.get(CONF_CLOSE_ENTITY),
            data.get(CONF_IMPULSE_ENTITY),
        ],
    )

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
        "name": name,
        "area": area,
        "display_name": f"{area} — {name}" if area and name else (area or name),
    }
