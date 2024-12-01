"""Config flow for YandexGPT integration."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import logging
from types import MappingProxyType
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
    ConfigEntry,
)
from homeassistant.const import CONF_LLM_HASS_API, CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.helpers import llm
from homeassistant.helpers.selector import (
    SelectOptionDict,
    TemplateSelector,
    NumberSelector,
    NumberSelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    DOMAIN,
    CONF_FOLDER_ID,
    CONF_PROMPT,
    CONF_RECOMMENDED,
    CONF_MAX_TOKENS,
    RECOMMENDED_MAX_TOKENS,
    CONF_TEMPERATURE,
    RECOMMENDED_TEMPERATURE,
    CONF_CHAT_MODEL,
    RECOMMENDED_CHAT_MODEL,
    DEFAULT_INSTRUCTIONS_PROMPT_RU,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_FOLDER_ID): str,
        vol.Required(CONF_API_KEY): str,
    }
)

RECOMMENDED_OPTIONS = {
    CONF_RECOMMENDED: True,
    CONF_PROMPT: DEFAULT_INSTRUCTIONS_PROMPT_RU,
}


class YandexGPTConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for YandexGPT."""

    VERSION = 1
    MINOR_VERSION = 2

    def __init__(self) -> None:
        """Initialize config flow."""
        self.catalog_id: str | None = None
        self.api_key: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""

        if user_input is not None:
            # TODO: Validate input
            return self.async_create_entry(
                title="YandexGPT",
                data=user_input,
                options=RECOMMENDED_OPTIONS,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Create the options flow."""
        return YandexGPTOptionsFlow(config_entry)


class YandexGPTOptionsFlow(OptionsFlow):
    """YandexGPT options flow."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self.last_rendered_recommended = config_entry.options.get(
            CONF_RECOMMENDED, False
        )

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        options: dict[str, Any] | MappingProxyType[str, Any] = self.config_entry.options

        if user_input is not None:
            if user_input[CONF_RECOMMENDED] == self.last_rendered_recommended:
                if user_input[CONF_LLM_HASS_API] == "none":
                    user_input.pop(CONF_LLM_HASS_API)
                return self.async_create_entry(title="", data=user_input)

            # Re-render the options again,
            # now with the recommended options shown/hidden
            self.last_rendered_recommended = user_input[CONF_RECOMMENDED]

            options = {
                CONF_RECOMMENDED: user_input[CONF_RECOMMENDED],
                CONF_PROMPT: user_input[CONF_PROMPT],
            }

        suggested_values = options.copy()
        if not suggested_values.get(CONF_PROMPT):
            suggested_values[CONF_PROMPT] = DEFAULT_INSTRUCTIONS_PROMPT_RU

        schema = self.add_suggested_values_to_schema(
            vol.Schema(yandexgpt_config_option_schema(self.hass, options)),
            suggested_values,
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )


def yandexgpt_config_option_schema(
    hass: HomeAssistant,
    options: dict[str, Any] | MappingProxyType[str, Any],
) -> dict:
    """Return a schema for YandexGPT completion options."""
    hass_apis: list[SelectOptionDict] = [
        SelectOptionDict(
            label="No access to devices / Без доступа к устройствам",
            value="none",
        )
    ]
    hass_apis.extend(
        SelectOptionDict(
            label=api.name,
            value=api.id,
        )
        for api in llm.async_get_apis(hass)
    )

    schema = {
        vol.Optional(CONF_PROMPT): TemplateSelector(),
        vol.Optional(CONF_LLM_HASS_API, default="none"): SelectSelector(
            SelectSelectorConfig(options=hass_apis)
        ),
        vol.Required(
            CONF_RECOMMENDED, default=options.get(CONF_RECOMMENDED, False)
        ): bool,
    }

    if options.get(CONF_RECOMMENDED):
        return schema

    models = [
        SelectOptionDict(label="YandexGPT Pro", value="yandexgpt/latest"),
        SelectOptionDict(label="YandexGPT Pro 32k", value="yandexgpt-32k/latest"),
        SelectOptionDict(label="YandexGPT Lite", value="yandexgpt-lite/latest"),
    ]

    schema.update(
        {
            vol.Optional(
                CONF_CHAT_MODEL,
                description={"suggested_value": options.get(CONF_CHAT_MODEL)},
                default=RECOMMENDED_CHAT_MODEL,
            ): SelectSelector(
                SelectSelectorConfig(mode=SelectSelectorMode.DROPDOWN, options=models)
            ),
            vol.Optional(
                CONF_TEMPERATURE,
                description={"suggested_value": options.get(CONF_TEMPERATURE)},
                default=RECOMMENDED_TEMPERATURE,
            ): NumberSelector(NumberSelectorConfig(min=0, max=1, step=0.05)),
            vol.Optional(
                CONF_MAX_TOKENS,
                description={"suggested_value": options.get(CONF_MAX_TOKENS)},
                default=RECOMMENDED_MAX_TOKENS,
            ): int,
        }
    )
    return schema
