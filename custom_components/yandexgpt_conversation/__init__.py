"""The YandexGPT integration."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import asyncio
import base64

import voluptuous as vol
from async_upnp_client import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_API_KEY
from homeassistant.core import HomeAssistant, SupportsResponse, ServiceCall, ServiceResponse
from homeassistant.helpers import config_validation as cv, selector
from homeassistant.helpers.typing import ConfigType
from yandex_cloud_ml_sdk import YCloudML

from .const import DOMAIN, CONF_FOLDER_ID, LOGGER

SERVICE_GENERATE_IMAGE = "generate_image"
PLATFORMS = (Platform.CONVERSATION,)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    def write_image_to_file(base64_img):
        file_name = "/tmp/1.jpg"
        with open(file_name, "wb") as file:
            file.write(base64.b64decode(base64_img))
        return file_name

    async def render_image(call: ServiceCall) -> ServiceResponse:
        """Render an image with YandexART."""

        entry_id = call.data["config_entry"]
        entry = hass.config_entries.async_get_entry(entry_id)

        settings = entry.runtime_data

        payload = {
            "modelUri": f"art://{settings[CONF_FOLDER_ID]}/yandex-art/latest",
            "generationOptions": {
                "seed": "1863",
                "aspectRatio": {
                    "widthRatio": "4",
                    "heightRatio": "3",
                },
            },
            "messages": [
                {
                    "weight": "1",
                    "text": call.data["prompt"],
                }
            ],
        }

        headers = {
            "Accept": "application/json",
            "Authorization": f"Api-Key {settings[CONF_API_KEY]}"
        }

        operation_id = None

        async with aiohttp.ClientSession() as session:
            async with session.post("https://llm.api.cloud.yandex.net/foundationModels/v1/imageGenerationAsync",
                                    headers=headers, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    LOGGER.debug(data)
                    operation_id = data["id"]
                else:
                    data = await resp.text()
                    LOGGER.debug(data)
                    raise Exception(f"Failed to send async request, status code: {resp.status}")

            base64_img = None

            async with aiohttp.ClientSession() as session:
                end_time = asyncio.get_event_loop().time() + 30
                while True:
                    # Check if the operation has timed out and if so, raise an exception
                    if asyncio.get_event_loop().time() > end_time:
                        raise TimeoutError(f"Operation timed out after 30 seconds")
                    # Polling the operation
                    async with session.get(f"https://llm.api.cloud.yandex.net/operations/{operation_id}",
                                           headers=headers) as resp:
                        # If the request was successful, return the completion result
                        # Otherwise, raise an exception
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get('done', False):
                                base64_img = data["response"]["image"]
                                break
                        else:
                            raise Exception(f"Failed to poll operation status, status code: {resp.status}")
                    await asyncio.sleep(1)

            file_name = await hass.async_add_executor_job(write_image_to_file, base64_img)

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
                vol.Required("prompt"): cv.string,
            }
        ),
        supports_response=SupportsResponse.ONLY,
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up YandexGPT from a config entry."""
    settings = {**entry.data, **entry.options}

    yandexgpt_sdk = YCloudML(folder_id=settings[CONF_FOLDER_ID], auth=settings[CONF_API_KEY])

    # FIXME: Clean up YandexART code
    entry.runtime_data = {"catalog_id": settings[CONF_FOLDER_ID], "api_key": settings[CONF_API_KEY]}
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = yandexgpt_sdk

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload YandexGPT."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
