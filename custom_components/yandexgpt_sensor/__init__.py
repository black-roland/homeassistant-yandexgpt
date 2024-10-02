"""The YandexGPT integration."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from yandex_gpt import YandexGPTConfigManagerForAPIKey, YandexGPT

from .const import (
    DOMAIN,
    CONF_CATALOG_ID,
    CONF_API_KEY,
    CONF_MODEL_TYPE,
)

PLATFORMS = (Platform.CONVERSATION,)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up YandexGPT from a config entry."""
    settings = {**entry.data, **entry.options}

    yandexgpt_config = YandexGPTConfigManagerForAPIKey(model_type=settings[CONF_MODEL_TYPE],
                                                       catalog_id=settings[CONF_CATALOG_ID],
                                                       api_key=settings[CONF_API_KEY])

    yandexgpt = YandexGPT(config_manager=yandexgpt_config)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = yandexgpt

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload YandexGPT."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
