"""Config flow for YandexGPT integration."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from types import MappingProxyType
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_API_KEY, CONF_LLM_HASS_API
from homeassistant.core import HomeAssistant
from homeassistant.helpers import llm
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TemplateSelector,
)

from .const import (
    CONF_ASYNCHRONOUS_MODE,
    CONF_CHAT_MODEL,
    CONF_ENABLE_SERVER_DATA_LOGGING,
    CONF_FOLDER_ID,
    CONF_MAX_TOKENS,
    CONF_MODEL_VERSION,
    CONF_PROMPT,
    CONF_RECOMMENDED,
    CONF_TEMPERATURE,
    DEFAULT_CHAT_MODEL,
    DEFAULT_ENABLE_SERVER_DATA_LOGGING,
    DEFAULT_INSTRUCTIONS_PROMPT_RU,
    DEFAULT_MODEL_VERSION,
    DOMAIN,
    RECOMMENDED_MAX_TOKENS,
    RECOMMENDED_TEMPERATURE,
)

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
    MINOR_VERSION = 3

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

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """User initiated reconfiguration."""

        entry = self._get_reconfigure_entry()

        if user_input is not None:
            return self.async_update_reload_and_abort(
                entry,
                data_updates=user_input,
            )

        return self.async_show_form(
            step_id="reconfigure",
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
                CONF_LLM_HASS_API: user_input[CONF_LLM_HASS_API],
                CONF_CHAT_MODEL: user_input[CONF_CHAT_MODEL],
            }

        suggested_values = options.copy()
        if not suggested_values.get(CONF_PROMPT):
            suggested_values[CONF_PROMPT] = DEFAULT_INSTRUCTIONS_PROMPT_RU

        if suggested_values.get(CONF_CHAT_MODEL):
            deprecated_model_name = suggested_values[CONF_CHAT_MODEL].split("/")[0]
            suggested_values[CONF_CHAT_MODEL] = deprecated_model_name

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
            label="No access to devices",
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

    model_names = [
        SelectOptionDict(label="YandexGPT Lite", value="yandexgpt-lite"),
        SelectOptionDict(label="YandexGPT Pro", value="yandexgpt"),
        SelectOptionDict(label="YandexGPT Pro 32k", value="yandexgpt-32k"),
        SelectOptionDict(label="Llama 8b", value="llama-lite"),
        SelectOptionDict(label="Llama 70b", value="llama"),
    ]

    schema = {
        vol.Optional(CONF_PROMPT): TemplateSelector(),
        vol.Optional(
            CONF_LLM_HASS_API,
            description={"suggested_value": options.get(CONF_LLM_HASS_API)},
            default="none",
        ): SelectSelector(
            SelectSelectorConfig(options=hass_apis, translation_key=CONF_LLM_HASS_API)
        ),
        vol.Optional(
            CONF_CHAT_MODEL,
            description={"suggested_value": options.get(CONF_CHAT_MODEL)},
            default=DEFAULT_CHAT_MODEL,
        ): SelectSelector(
            SelectSelectorConfig(mode=SelectSelectorMode.DROPDOWN, options=model_names)
        ),
        vol.Required(
            CONF_ENABLE_SERVER_DATA_LOGGING,
            default=options.get(
                CONF_ENABLE_SERVER_DATA_LOGGING, DEFAULT_ENABLE_SERVER_DATA_LOGGING
            ),
        ): bool,
        vol.Required(
            CONF_RECOMMENDED, default=options.get(CONF_RECOMMENDED, False)
        ): bool,
    }

    if options.get(CONF_RECOMMENDED):
        return schema

    model_versions = [
        SelectOptionDict(label="Deprecated", value="deprecated"),
        SelectOptionDict(label="Latest", value="latest"),
        SelectOptionDict(label="Release Candidate", value="rc"),
    ]

    schema.update(
        {
            vol.Optional(
                CONF_MODEL_VERSION,
                description={"suggested_value": options.get(CONF_MODEL_VERSION)},
                default=DEFAULT_MODEL_VERSION,
            ): SelectSelector(
                SelectSelectorConfig(
                    mode=SelectSelectorMode.DROPDOWN, options=model_versions
                )
            ),
            vol.Optional(
                CONF_TEMPERATURE,
                description={"suggested_value": options.get(CONF_TEMPERATURE)},
                default=RECOMMENDED_TEMPERATURE,
            ): NumberSelector(NumberSelectorConfig(min=0, max=1, step=0.05)),
            vol.Optional(
                CONF_ASYNCHRONOUS_MODE,
                description={"suggested_value": options.get(CONF_ASYNCHRONOUS_MODE)},
                default=options.get(CONF_ASYNCHRONOUS_MODE, False),
            ): bool,
            vol.Optional(
                CONF_MAX_TOKENS,
                description={"suggested_value": options.get(CONF_MAX_TOKENS)},
                default=RECOMMENDED_MAX_TOKENS,
            ): int,
        }
    )
    return schema
