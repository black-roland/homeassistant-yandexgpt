"""Constants for the YandexGPT Conversation integration."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging

DOMAIN = "yandexgpt_conversation"
LOGGER = logging.getLogger(__package__)

CONF_FOLDER_ID = "folder_id"
CONF_PROMPT = "prompt"
CONF_RECOMMENDED = "recommended"
CONF_MAX_TOKENS = "max_tokens"
CONF_TEMPERATURE = "temperature"
CONF_CHAT_MODEL = "chat_model"
CONF_MODEL_VERSION = "model_version"
CONF_ASYNCHRONOUS_MODE = "asynchronous_mode"
CONF_ENABLE_SERVER_DATA_LOGGING = "enable_server_data_logging"
DEFAULT_CHAT_MODEL = "yandexgpt-lite"
DEFAULT_MODEL_VERSION = "latest"
DEFAULT_ENABLE_SERVER_DATA_LOGGING = True
RECOMMENDED_MAX_TOKENS = 1024
RECOMMENDED_TEMPERATURE = 0.6

DEFAULT_INSTRUCTIONS_PROMPT_RU = """Ты — голосовой ассистент для Home Assistant.
Отвечай на вопросы правдиво.
Отвечай простым текстом, кратко и по существу.
"""

ASSIST_UNSUPPORTED_MODELS = ["llama-lite"]
ASSIST_PARTIALLY_SUPPORTED_MODELS = ["llama", "yandexgpt-lite"]

ATTR_FILENAME = "file_name"
ATTR_SEED = "seed"
ATTR_PROMPT = "prompt"
