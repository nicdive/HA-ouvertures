"""Constantes pour l'intégration Gestion des ouvertures."""

from __future__ import annotations

DOMAIN = "ouvertures"
CONF_OPENING_TYPE = "opening_type"
CONF_NAME = "name"
CONF_CONTACT_ENTITY = "contact_entity"
CONF_SHUTTER_ENTITY = "shutter_entity"
CONF_OPEN_ENTITY = "open_entity"
CONF_CLOSE_ENTITY = "close_entity"
CONF_IMPULSE_ENTITY = "impulse_entity"
CONF_INVERTED = "inverted"

TYPE_BAIE = "baie_vitree"
TYPE_FENETRE_SIMPLE = "fenetre_simple"
TYPE_FENETRE_SIMPLE_VOLETS = "fenetre_simple_volets"
TYPE_FENETRE_DOUBLE = "fenetre_double"
TYPE_FENETRE_DOUBLE_VOLETS = "fenetre_double_volets"
TYPE_PORTE_FENETRE_3 = "porte_fenetre_3_battants"
TYPE_PORTE = "porte"
TYPE_PORTAIL = "portail_coulissant"
TYPE_GARAGE = "garage_sectionnelle"
TYPE_PISCINE = "piscine_volet"

OPENING_TYPES = {
    TYPE_BAIE: {
        "label": "Baie vitrée",
        "icon": "mdi:door-sliding",
        "needs_shutter": True,
        "needs_open": False,
        "needs_close": False,
        "needs_impulse": False,
    },
    TYPE_FENETRE_SIMPLE: {
        "label": "Fenêtre simple battant",
        "icon": "mdi:window-closed-variant",
        "needs_shutter": False,
        "needs_open": False,
        "needs_close": False,
        "needs_impulse": False,
    },
    TYPE_FENETRE_SIMPLE_VOLETS: {
        "label": "Fenêtre simple battant + volets",
        "icon": "mdi:window-shutter",
        "needs_shutter": True,
        "needs_open": False,
        "needs_close": False,
        "needs_impulse": False,
    },
    TYPE_FENETRE_DOUBLE: {
        "label": "Fenêtre double battant",
        "icon": "mdi:window-closed-variant",
        "needs_shutter": False,
        "needs_open": False,
        "needs_close": False,
        "needs_impulse": False,
    },
    TYPE_FENETRE_DOUBLE_VOLETS: {
        "label": "Fenêtre double battant + volets",
        "icon": "mdi:window-shutter",
        "needs_shutter": True,
        "needs_open": False,
        "needs_close": False,
        "needs_impulse": False,
    },
    TYPE_PORTE_FENETRE_3: {
        "label": "Porte-fenêtre 3 battants (haut arrondi + volet roulant)",
        "icon": "mdi:door-sliding-open",
        "needs_shutter": True,
        # État du volet = entité cover (volet roulant), pas un binary_sensor
        "shutter_cover_only": True,
        "needs_open": False,
        "needs_close": False,
        "needs_impulse": False,
    },
    TYPE_PORTE: {
        "label": "Porte simple",
        "icon": "mdi:door",
        "needs_shutter": False,
        "needs_open": False,
        "needs_close": False,
        "needs_impulse": False,
    },
    TYPE_PORTAIL: {
        "label": "Portail coulissant",
        "icon": "mdi:gate",
        "needs_shutter": False,
        "needs_open": True,
        "needs_close": True,
        "needs_impulse": True,
    },
    TYPE_GARAGE: {
        "label": "Porte de garage sectionnelle",
        "icon": "mdi:garage",
        "needs_shutter": False,
        "needs_open": False,
        "needs_close": False,
        "needs_impulse": True,
    },
    TYPE_PISCINE: {
        "label": "Volet piscine",
        "icon": "mdi:pool",
        "needs_shutter": False,
        "needs_open": False,
        "needs_close": False,
        "needs_impulse": False,
    },
}

TYPES_WITH_SHUTTERS = frozenset(
    {
        TYPE_BAIE,
        TYPE_FENETRE_SIMPLE_VOLETS,
        TYPE_FENETRE_DOUBLE_VOLETS,
        TYPE_PORTE_FENETRE_3,
    }
)

# États combinés baie/fenêtre + volets
STATE_FERMEE_VOLETS_OUVERTS = "fermee_volets_ouverts"
STATE_OUVERTE_VOLETS_OUVERTS = "ouverte_volets_ouverts"
STATE_FERMEE_VOLETS_FERMES = "fermee_volets_fermes"
STATE_OUVERTE_VOLETS_FERMES = "ouverte_volets_fermes"
STATE_FERME = "ferme"
STATE_OUVERT = "ouvert"
STATE_INCONNU = "inconnu"

OPEN_STATES = frozenset(
    {
        "on",
        "open",
        "opening",
        "unlocked",
        "true",
        "1",
        "ouvert",
        "ouverte",
    }
)

CLOSED_STATES = frozenset(
    {
        "off",
        "closed",
        "closing",
        "locked",
        "false",
        "0",
        "ferme",
        "fermee",
        "fermé",
        "fermée",
    }
)

STATIC_URL_PATH = f"/{DOMAIN}_static"
CARD_FILENAME = "ouvertures-card.js"
# Incrémenter pour forcer le rechargement des SVG / JS côté navigateur
ASSETS_VERSION = "1.4.1"

ATTR_OPENING_TYPE = "opening_type"
ATTR_CONTACT_ENTITY = "contact_entity"
ATTR_SHUTTER_ENTITY = "shutter_entity"
ATTR_OPEN_ENTITY = "open_entity"
ATTR_CLOSE_ENTITY = "close_entity"
ATTR_IMPULSE_ENTITY = "impulse_entity"
ATTR_IMAGE = "image"
ATTR_IS_OPEN = "is_open"
ATTR_IS_ALERT = "is_alert"
ATTR_SHUTTER_OPEN = "shutter_open"
ATTR_LABEL = "label"
ATTR_AREA = "area"
ATTR_DISPLAY_NAME = "display_name"
