"""Config flow pour Gestion des ouvertures."""

from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_CLOSE_ENTITY,
    CONF_CONTACT_ENTITY,
    CONF_IMPULSE_ENTITY,
    CONF_INVERTED,
    CONF_OPEN_ENTITY,
    CONF_OPENING_TYPE,
    CONF_SHUTTER_ENTITY,
    DOMAIN,
    OPENING_TYPES,
    TYPE_BAIE,
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

# Volet roulant : uniquement une entité cover (état open/closed / position)
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


def _shutter_selector(opening_type: str) -> selector.EntitySelector:
    meta = OPENING_TYPES[opening_type]
    if meta.get("shutter_cover_only"):
        return ROLLER_COVER_SELECTOR
    return SHUTTER_SELECTOR


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
            return self.async_show_form(step_id="user", data_schema=_type_schema())

        self._name = user_input[CONF_NAME].strip()
        self._opening_type = user_input[CONF_OPENING_TYPE]
        self._inverted = bool(user_input.get(CONF_INVERTED, False))

        if not self._name:
            return self.async_show_form(
                step_id="user",
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

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
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
