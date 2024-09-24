"""The YandexGPT integration."""

from __future__ import annotations

import asyncio
import logging

import httpx

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.util.ssl import get_default_context
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


async def async_unload_entry(_hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload YandexGPT."""
    # if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
    #     return False
    # hass.data[DOMAIN].pop(entry.entry_id)
    return True
