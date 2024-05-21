# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging
from typing import Any

import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import (
    CONF_NAME,
)
from homeassistant.core import HomeAssistant, CoreState
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import dt as dt_util
from lru import LRU
from yandex_gpt import YandexGPT, YandexGPTConfigManagerForAPIKey

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "YandexGpt completion"

CONF_CATALOG_ID = "catalog_id"
CONF_API_KEY = "api_key"

CONF_SYSTEM_PROMPT = "system_prompt"
CONF_USER_PROMPT = "user_prompt"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_CATALOG_ID): cv.string,
        vol.Required(CONF_API_KEY): cv.string,
        vol.Required(CONF_SYSTEM_PROMPT): cv.string,
        vol.Required(CONF_USER_PROMPT): cv.template,
    }
)


def setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None,
) -> None:
    name = config.get(CONF_NAME)

    system_prompt = config.get(CONF_SYSTEM_PROMPT)
    user_prompt = config.get(CONF_USER_PROMPT)

    # TODO: Change sensor configuration to make it look like the new template sensor configuration
    #       so this should be initialized only once
    yandexgpt_config = YandexGPTConfigManagerForAPIKey(model_type="yandexgpt-lite",
                                                       catalog_id=config.get(CONF_CATALOG_ID),
                                                       api_key=config.get(CONF_API_KEY))
    yandexgpt = YandexGPT(config_manager=yandexgpt_config)

    device = YandexGptSensor(yandexgpt, name, system_prompt, user_prompt)

    add_entities([device], True)


class YandexGptSensor(SensorEntity):
    _attr_should_poll = False

    def __init__(self, yandexgpt, name, system_prompt, user_prompt):
        self._name = name
        self._state = None
        self._state_attributes = None

        self._yandexgpt = yandexgpt
        self._system_prompt = system_prompt
        self._user_prompt_tpl = user_prompt
        self._cache = LRU(32)
        self._completion = None
        self._last_updated = None

        self._yandexgpt = yandexgpt

    @property
    def name(self):
        return self._name

    @property
    def native_value(self):
        return self._last_updated

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs = {"completion": self._completion}
        return attrs

    async def async_update(self) -> None:
        # Ignore update on HASS restart to reduce API requests
        if self.hass.state == CoreState.not_running:
            return

        # TODO: Render system prompt as template
        user_prompt = self._user_prompt_tpl.async_render()

        cache_key = (self._system_prompt, user_prompt)
        if (completion := self._cache.get(cache_key)) is None:
            completion = await self.get_ai_completion(self._system_prompt, user_prompt)
            self._cache[cache_key] = completion
            self._completion = completion
            self._last_updated = dt_util.utcnow().isoformat()
        else:
            self._completion = completion

    async def get_ai_completion(self, system_prompt, user_prompt) -> str:
        _LOGGER.debug("Sending completion request...",
                      extra={"system_prompt": system_prompt, "user_prompt": user_prompt})
        return await self._yandexgpt.get_async_completion(
            messages=[
                {"role": "system", "text": system_prompt},
                {"role": "user", "text": user_prompt},
            ],
            max_tokens=180,
            timeout=30,
        )
