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
CONF_ENABLE_SERVER_DATA_LOGGING = "enable_server_data_logging"
CONF_ASYNCHRONOUS_MODE = "asynchronous_mode"
CONF_NO_HA_DEFAULT_PROMPT = "no_ha_default_prompt"
DEFAULT_CHAT_MODEL = "yandexgpt-lite"
DEFAULT_MODEL_VERSION = "latest"
DEFAULT_NO_HA_DEFAULT_PROMPT = False
DEFAULT_ENABLE_SERVER_DATA_LOGGING = True
RECOMMENDED_MAX_TOKENS = 1024
RECOMMENDED_TEMPERATURE = 0.6

DEFAULT_INSTRUCTIONS_PROMPT_RU = """Ты — голосовой ассистент для Home Assistant.
Отвечай на вопросы правдиво. Отвечай кратко, чётко и на русском языке.
"""

CHAT_MODELS = (
    ("yandexgpt-lite", "YandexGPT Lite"),
    ("yandexgpt", "YandexGPT Pro"),
    ("llama-lite", "Llama 8B"),
    ("llama", "Llama 70B"),
    ("qwen3-235b-a22b-fp8", "Qwen3 235B"),
    ("gpt-oss-120b", "gpt-oss-120b"),
    ("gpt-oss-20b", "gpt-oss-20b"),
)

ASSIST_UNSUPPORTED_MODELS = ["llama-lite"]
ASSIST_PARTIALLY_SUPPORTED_MODELS = ["llama", "yandexgpt-lite"]

ATTR_FILENAME = "file_name"
ATTR_SEED = "seed"
ATTR_PROMPT = "prompt"
