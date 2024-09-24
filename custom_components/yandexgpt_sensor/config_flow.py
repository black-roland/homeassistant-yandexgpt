"""Config flow for YandexGPT integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_CATALOG_ID,
    CONF_API_KEY,
    CONF_MODEL_TYPE,
)

_LOGGER = logging.getLogger(__name__)

STEP_API_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CATALOG_ID): str,
        vol.Required(CONF_API_KEY): str,
        vol.Required(CONF_MODEL_TYPE): str,
    }
)


class YandexGPTConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for YandexGPT."""

    VERSION = 1
    MINOR_VERSION = 2

    def __init__(self) -> None:
        """Initialize config flow."""
        self.catalog_id: str | None = None
        self.api_key: str | None = None
        self.model_type: str | None = None

    async def async_step_user(
            self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""

        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_API_DATA_SCHEMA,
                # errors=errors,
            )

        user_input = user_input or {}

        # errors: dict[str, str] = {}

        # TODO: Validate input

        return self.async_create_entry(
            title="YandexGPT",
            data=user_input,
        )


class YandexGPTOptionsFlow(OptionsFlow):
    """YandexGPT options flow."""

    async def async_step_done(self, _: dict[str, Any] | None = None) -> FlowResult:
        """Finish the flow."""
        return self.async_create_entry(title="", data={})
