"""The YandexGPT integration."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import base64

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import selector
from homeassistant.helpers.typing import ConfigType
from yandex_cloud_ml_sdk import YCloudML

from .const import CONF_FOLDER_ID, DOMAIN
from .yandexart import YandexArt

SERVICE_GENERATE_IMAGE = "generate_image"
PLATFORMS = (Platform.CONVERSATION,)
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    def write_image_to_file(base64_img: str, file_name: str) -> str:
        with open(file_name, "wb") as file:
            file.write(base64.b64decode(base64_img))
        return file_name

    async def render_image(call: ServiceCall) -> ServiceResponse:
        """Render an image with YandexART."""

        entry_id = call.data["config_entry"]
        entry = hass.config_entries.async_get_entry(entry_id)

        settings = {**entry.data, **entry.options}
        yandexart = YandexArt(
            folder_id=settings[CONF_FOLDER_ID], api_key=settings[CONF_API_KEY]
        )
        base64_img = await yandexart.generate(call.data["seed"], call.data["prompt"])

        file_name = await hass.async_add_executor_job(
            write_image_to_file, base64_img, call.data["file_name"]
        )

        return {"file_name": file_name}

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
                vol.Required("seed"): vol.All(vol.Coerce(int), vol.Clamp(min=0)),
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

    yandexgpt_sdk = YCloudML(
        folder_id=settings[CONF_FOLDER_ID], auth=settings[CONF_API_KEY]
    )

    entry.runtime_data = yandexgpt_sdk

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload YandexGPT."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
