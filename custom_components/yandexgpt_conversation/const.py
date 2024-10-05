"""Constants for the YandexGPT Conversation integration."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging

DOMAIN = "yandexgpt_conversation"
LOGGER = logging.getLogger(__package__)

CONF_CATALOG_ID = "catalog_id"
CONF_MODEL_TYPE = "model_type"
DEFAULT_MODEL = "yandexgpt-lite"

CONF_PROMPT = "prompt"
CONF_RECOMMENDED = "recommended"
CONF_MAX_TOKENS = "max_tokens"
RECOMMENDED_MAX_TOKENS = 1024
CONF_TEMPERATURE = "temperature"
RECOMMENDED_TEMPERATURE = 1.0
