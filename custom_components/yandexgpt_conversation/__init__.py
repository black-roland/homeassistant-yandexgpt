"""The YandexGPT integration."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import (HomeAssistant, ServiceCall, ServiceResponse,
                                SupportsResponse)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import selector
from homeassistant.helpers.typing import ConfigType
from yandex_cloud_ml_sdk import AsyncYCloudML

from .const import (ATTR_FILENAME, ATTR_PROMPT, ATTR_SEED,
                    CONF_ENABLE_SERVER_DATA_LOGGING, CONF_FOLDER_ID,
                    DEFAULT_ENABLE_SERVER_DATA_LOGGING, DOMAIN, LOGGER)

SERVICE_GENERATE_IMAGE = "generate_image"
PLATFORMS = (Platform.CONVERSATION,)
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, entry: ConfigType) -> bool:
    def write_image_to_file(image_bytes: bytes, file_name: str) -> str:
        try:
            LOGGER.debug("Writing image to file: %s...", file_name)
            with open(file_name, "wb") as file:
                file.write(image_bytes)
            return file_name
        except Exception as e:
            LOGGER.error("Failed to write image to file %s: %s", file_name, str(e))
            raise

    async def render_image(call: ServiceCall) -> ServiceResponse:
        """Render an image with YandexART."""
        LOGGER.debug("Starting image generation with seed: %s, prompt: %s",
                     call.data[ATTR_SEED], call.data[ATTR_PROMPT])

        if not hass.config.is_allowed_path(call.data[ATTR_FILENAME]):
            raise HomeAssistantError(
                f"Cannot write `{call.data[ATTR_FILENAME]}`, no access to path; `allowlist_external_dirs` may need to be adjusted in `configuration.yaml`")  # noqa: E501

        entry_id = call.data["config_entry"]
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is None:
            raise HomeAssistantError(f"Config entry {entry_id} not found")

        try:
            client = entry.runtime_data

            model = client.models.image_generation("yandex-art")
            model = model.configure(seed=int(call.data[ATTR_SEED]))

            LOGGER.debug("Sending generation request...")
            operation = await model.run_deferred(call.data[ATTR_PROMPT])

            LOGGER.debug("Waiting for image generation to complete...")
            result = await operation

            file_name = await hass.async_add_executor_job(
                write_image_to_file, result.image_bytes, call.data[ATTR_FILENAME])
            LOGGER.debug("Successfully saved image to: %s", file_name)

            return {"file_name": file_name}

        except Exception as err:
            LOGGER.error("Error during image generation: %s", str(err), exc_info=True)
            raise HomeAssistantError(f"Image generation failed: {str(err)}") from err

    hass.services.async_register(
        DOMAIN,
        SERVICE_GENERATE_IMAGE,
        render_image,
        schema=vol.Schema(
            {
                vol.Required("config_entry"): selector.ConfigEntrySelector(
                    {
                        "integration": DOMAIN,
                    }
                ),
                vol.Required("seed"): vol.All(
                    vol.Coerce(str), cv.matches_regex(r"[0-9]+")
                ),
                vol.Required("prompt"): cv.string,
                vol.Required("file_name"): cv.path,
            }
        ),
        supports_response=SupportsResponse.ONLY,
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up YandexGPT from a config entry."""
    settings = {**entry.data, **entry.options}

    entry.runtime_data = AsyncYCloudML(
        folder_id=settings[CONF_FOLDER_ID],
        auth=settings[CONF_API_KEY],
        enable_server_data_logging=settings.get(
            CONF_ENABLE_SERVER_DATA_LOGGING, DEFAULT_ENABLE_SERVER_DATA_LOGGING
        ),
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload YandexGPT."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
