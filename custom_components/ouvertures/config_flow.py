"""Config flow pour Gestion des ouvertures."""

from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector

from .alert import list_opening_options
from .const import (
    ALERT_DEFAULT_BRIGHTNESS,
    ALERT_DEFAULT_COLOR,
    ALERT_DEFAULT_NAME,
    ALERT_UNIQUE_ID,
    CONF_ALERT_BRIGHTNESS,
    CONF_ALERT_COLOR,
    CONF_ALERT_ENABLED,
    CONF_ALERT_GATEWAY,
    CONF_ALERT_MONITORED,
    CONF_ALERT_TRIGGER,
    CONF_CLOSE_ENTITY,
    CONF_CONTACT_ENTITY,
    CONF_IMPULSE_ENTITY,
    CONF_INVERTED,
    CONF_OPEN_ENTITY,
    CONF_OPENING_TYPE,
    CONF_SETUP_KIND,
    CONF_SHUTTER_ENTITY,
    DOMAIN,
    OPENING_TYPES,
    SETUP_KIND_ALERT,
    SETUP_KIND_OPENING,
    TYPE_ALERTE_RESTEE,
    TYPE_BAIE,
    TYPES_ALERT_MONITORABLE,
    TYPES_ALERT_TRIGGER,
)

CONTACT_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(
        domain=["binary_sensor", "sensor", "cover", "input_boolean", "switch"],
        multiple=False,
    )
)

SHUTTER_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(
        domain=["cover", "binary_sensor", "sensor", "input_boolean", "switch"],
        multiple=False,
    )
)

ROLLER_COVER_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(
        domain=["cover"],
        multiple=False,
    )
)

ACTION_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(
        domain=["button", "switch", "cover", "script", "input_button", "scene"],
        multiple=False,
    )
)

LIGHT_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(
        domain=["light"],
        multiple=False,
    )
)


def _shutter_selector(opening_type: str) -> selector.EntitySelector:
    meta = OPENING_TYPES[opening_type]
    if meta.get("shutter_cover_only"):
        return ROLLER_COVER_SELECTOR
    return SHUTTER_SELECTOR


def _kind_schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_SETUP_KIND, default=SETUP_KIND_OPENING): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        {
                            "value": SETUP_KIND_OPENING,
                            "label": "Nouvelle ouverture (baie, fenêtre, porte…)",
                        },
                        {
                            "value": SETUP_KIND_ALERT,
                            "label": "Alerte ouverture restée ouverte (gateway)",
                        },
                    ],
                    mode=selector.SelectSelectorMode.LIST,
                )
            ),
        }
    )


def _type_schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NAME): str,
            vol.Required(CONF_OPENING_TYPE, default=TYPE_BAIE): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        {"value": key, "label": meta["label"]}
                        for key, meta in OPENING_TYPES.items()
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(CONF_INVERTED, default=False): bool,
        }
    )


def _entities_schema(opening_type: str) -> vol.Schema:
    meta = OPENING_TYPES[opening_type]
    fields: dict[Any, Any] = {
        vol.Required(CONF_CONTACT_ENTITY): CONTACT_SELECTOR,
    }
    if meta["needs_shutter"]:
        fields[vol.Required(CONF_SHUTTER_ENTITY)] = _shutter_selector(opening_type)
    if meta["needs_open"]:
        fields[vol.Required(CONF_OPEN_ENTITY)] = ACTION_SELECTOR
    if meta["needs_close"]:
        fields[vol.Required(CONF_CLOSE_ENTITY)] = ACTION_SELECTOR
    if meta["needs_impulse"]:
        fields[vol.Required(CONF_IMPULSE_ENTITY)] = ACTION_SELECTOR
    return vol.Schema(fields)


def _alert_schema(
    monitored_options: list[dict[str, str]],
    trigger_options: list[dict[str, str]],
    current: dict[str, Any] | None = None,
) -> vol.Schema:
    current = current or {}
    mon_default = current.get(CONF_ALERT_MONITORED) or []
    # filtrer les IDs encore valides
    valid_mon = {o["value"] for o in monitored_options}
    mon_default = [x for x in mon_default if x in valid_mon]
    trig_default = current.get(CONF_ALERT_TRIGGER)
    valid_trig = {o["value"] for o in trigger_options}
    if trig_default not in valid_trig:
        trig_default = trigger_options[0]["value"] if trigger_options else None

    fields: dict[Any, Any] = {
        vol.Optional(
            CONF_ALERT_ENABLED,
            default=bool(current.get(CONF_ALERT_ENABLED, True)),
        ): bool,
    }
    if monitored_options:
        fields[
            vol.Required(
                CONF_ALERT_MONITORED,
                default=mon_default,
            )
        ] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=monitored_options,
                multiple=True,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        )
    if trigger_options and trig_default is not None:
        fields[
            vol.Required(
                CONF_ALERT_TRIGGER,
                default=trig_default,
            )
        ] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=trigger_options,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        )
    gateway = current.get(CONF_ALERT_GATEWAY)
    if gateway:
        fields[vol.Required(CONF_ALERT_GATEWAY, default=gateway)] = LIGHT_SELECTOR
    else:
        fields[vol.Required(CONF_ALERT_GATEWAY)] = LIGHT_SELECTOR
    fields[
        vol.Optional(
            CONF_ALERT_COLOR,
            default=list(current.get(CONF_ALERT_COLOR) or ALERT_DEFAULT_COLOR),
        )
    ] = selector.ColorRGBSelector()
    fields[
        vol.Optional(
            CONF_ALERT_BRIGHTNESS,
            default=int(current.get(CONF_ALERT_BRIGHTNESS, ALERT_DEFAULT_BRIGHTNESS)),
        )
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=1,
            max=255,
            mode=selector.NumberSelectorMode.SLIDER,
        )
    )
    return vol.Schema(fields)


class OuverturesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Flux de configuration."""

    VERSION = 1

    def __init__(self) -> None:
        self._name: str | None = None
        self._opening_type: str | None = None
        self._inverted: bool = False

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=_kind_schema())

        kind = user_input.get(CONF_SETUP_KIND, SETUP_KIND_OPENING)
        if kind == SETUP_KIND_ALERT:
            return await self.async_step_alert()
        return await self.async_step_opening()

    async def async_step_opening(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input is None:
            return self.async_show_form(step_id="opening", data_schema=_type_schema())

        self._name = user_input[CONF_NAME].strip()
        self._opening_type = user_input[CONF_OPENING_TYPE]
        self._inverted = bool(user_input.get(CONF_INVERTED, False))

        if not self._name:
            return self.async_show_form(
                step_id="opening",
                data_schema=_type_schema(),
                errors={"base": "invalid_name"},
            )

        await self.async_set_unique_id(
            f"{DOMAIN}_{self._opening_type}_{self._name.lower().replace(' ', '_')}"
        )
        self._abort_if_unique_id_configured()
        return await self.async_step_entities()

    async def async_step_entities(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        assert self._opening_type is not None
        assert self._name is not None

        if user_input is None:
            return self.async_show_form(
                step_id="entities",
                data_schema=_entities_schema(self._opening_type),
                description_placeholders={
                    "name": self._name,
                    "type": OPENING_TYPES[self._opening_type]["label"],
                },
            )

        data = {
            CONF_NAME: self._name,
            CONF_OPENING_TYPE: self._opening_type,
            CONF_INVERTED: self._inverted,
            **user_input,
        }
        return self.async_create_entry(title=self._name, data=data)

    async def async_step_alert(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        await self.async_set_unique_id(ALERT_UNIQUE_ID)
        self._abort_if_unique_id_configured()

        monitored = list_opening_options(
            self.hass, allowed_types=TYPES_ALERT_MONITORABLE
        )
        triggers = list_opening_options(self.hass, allowed_types=TYPES_ALERT_TRIGGER)
        errors: dict[str, str] = {}

        if user_input is not None:
            if not monitored:
                errors["base"] = "no_monitored"
            elif not triggers:
                errors["base"] = "no_trigger"
            elif not user_input.get(CONF_ALERT_MONITORED):
                errors[CONF_ALERT_MONITORED] = "required_monitored"
            elif not user_input.get(CONF_ALERT_TRIGGER):
                errors[CONF_ALERT_TRIGGER] = "required_trigger"
            elif not user_input.get(CONF_ALERT_GATEWAY):
                errors[CONF_ALERT_GATEWAY] = "required_gateway"
            else:
                data = {
                    CONF_NAME: ALERT_DEFAULT_NAME,
                    CONF_OPENING_TYPE: TYPE_ALERTE_RESTEE,
                    CONF_ALERT_ENABLED: bool(
                        user_input.get(CONF_ALERT_ENABLED, True)
                    ),
                    CONF_ALERT_MONITORED: user_input[CONF_ALERT_MONITORED],
                    CONF_ALERT_TRIGGER: user_input[CONF_ALERT_TRIGGER],
                    CONF_ALERT_GATEWAY: user_input[CONF_ALERT_GATEWAY],
                    CONF_ALERT_COLOR: user_input.get(
                        CONF_ALERT_COLOR, list(ALERT_DEFAULT_COLOR)
                    ),
                    CONF_ALERT_BRIGHTNESS: int(
                        user_input.get(
                            CONF_ALERT_BRIGHTNESS, ALERT_DEFAULT_BRIGHTNESS
                        )
                    ),
                }
                return self.async_create_entry(title=ALERT_DEFAULT_NAME, data=data)

        return self.async_show_form(
            step_id="alert",
            data_schema=_alert_schema(monitored, triggers),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        if config_entry.data.get(CONF_OPENING_TYPE) == TYPE_ALERTE_RESTEE:
            return AlertOptionsFlow()
        return OuverturesOptionsFlow()


class OuverturesOptionsFlow(config_entries.OptionsFlow):
    """Options pour modifier les entités liées."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        opening_type = self.config_entry.data[CONF_OPENING_TYPE]
        current = {**self.config_entry.data, **self.config_entry.options}

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        meta = OPENING_TYPES[opening_type]
        fields: dict[Any, Any] = {
            vol.Required(
                CONF_CONTACT_ENTITY,
                default=current.get(CONF_CONTACT_ENTITY),
            ): CONTACT_SELECTOR,
            vol.Optional(
                CONF_INVERTED,
                default=bool(current.get(CONF_INVERTED, False)),
            ): bool,
        }
        if meta["needs_shutter"]:
            fields[
                vol.Required(
                    CONF_SHUTTER_ENTITY,
                    default=current.get(CONF_SHUTTER_ENTITY),
                )
            ] = _shutter_selector(opening_type)
        if meta["needs_open"]:
            fields[
                vol.Required(
                    CONF_OPEN_ENTITY,
                    default=current.get(CONF_OPEN_ENTITY),
                )
            ] = ACTION_SELECTOR
        if meta["needs_close"]:
            fields[
                vol.Required(
                    CONF_CLOSE_ENTITY,
                    default=current.get(CONF_CLOSE_ENTITY),
                )
            ] = ACTION_SELECTOR
        if meta["needs_impulse"]:
            fields[
                vol.Required(
                    CONF_IMPULSE_ENTITY,
                    default=current.get(CONF_IMPULSE_ENTITY),
                )
            ] = ACTION_SELECTOR

        return self.async_show_form(step_id="init", data_schema=vol.Schema(fields))


class AlertOptionsFlow(config_entries.OptionsFlow):
    """Options de l'alerte restée ouverte."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        current = {**self.config_entry.data, **self.config_entry.options}
        monitored = list_opening_options(
            self.hass, allowed_types=TYPES_ALERT_MONITORABLE
        )
        triggers = list_opening_options(self.hass, allowed_types=TYPES_ALERT_TRIGGER)
        errors: dict[str, str] = {}

        if user_input is not None:
            if not user_input.get(CONF_ALERT_MONITORED):
                errors[CONF_ALERT_MONITORED] = "required_monitored"
            elif not user_input.get(CONF_ALERT_TRIGGER):
                errors[CONF_ALERT_TRIGGER] = "required_trigger"
            elif not user_input.get(CONF_ALERT_GATEWAY):
                errors[CONF_ALERT_GATEWAY] = "required_gateway"
            else:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_ALERT_ENABLED: bool(
                            user_input.get(CONF_ALERT_ENABLED, True)
                        ),
                        CONF_ALERT_MONITORED: user_input[CONF_ALERT_MONITORED],
                        CONF_ALERT_TRIGGER: user_input[CONF_ALERT_TRIGGER],
                        CONF_ALERT_GATEWAY: user_input[CONF_ALERT_GATEWAY],
                        CONF_ALERT_COLOR: user_input.get(
                            CONF_ALERT_COLOR, list(ALERT_DEFAULT_COLOR)
                        ),
                        CONF_ALERT_BRIGHTNESS: int(
                            user_input.get(
                                CONF_ALERT_BRIGHTNESS, ALERT_DEFAULT_BRIGHTNESS
                            )
                        ),
                    },
                )

        return self.async_show_form(
            step_id="init",
            data_schema=_alert_schema(monitored, triggers, current),
            errors=errors,
        )
