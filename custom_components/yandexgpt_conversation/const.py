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
CONF_MAX_TOOL_ITERATIONS = "max_tool_iterations"
CONF_NO_HA_DEFAULT_PROMPT = "no_ha_default_prompt"
DEFAULT_CHAT_MODEL = "yandexgpt-lite"
DEFAULT_MODEL_VERSION = "latest"
DEFAULT_NO_HA_DEFAULT_PROMPT = False
DEFAULT_ENABLE_SERVER_DATA_LOGGING = True
DEFAULT_MAX_TOOL_ITERATIONS = 10
RECOMMENDED_MAX_TOKENS = 1024
RECOMMENDED_TEMPERATURE = 0.6

DEFAULT_INSTRUCTIONS_PROMPT_RU = """Ты — голосовой ассистент для Home Assistant.
Отвечай на вопросы правдиво. Отвечай кратко, чётко и на русском языке.
"""

CHAT_MODELS = (
    ("yandexgpt-lite", "YandexGPT Lite"),
    ("yandexgpt", "YandexGPT Pro"),
    ("aliceai-llm", "Alice AI LLM"),
)

ASSIST_UNSUPPORTED_MODELS = []
ASSIST_PARTIALLY_SUPPORTED_MODELS = ["yandexgpt-lite"]

DOC_CHAT_MODELS_URL = "https://aistudio.yandex.ru/docs/ai-studio/concepts/generation/models"
DOC_PRICING_URL = "https://aistudio.yandex.ru/docs/ai-studio/pricing#common-instance-sync"
DOC_PROMPT_TEMPLATES_URL = "https://github.com/black-roland/homeassistant-yandexgpt/wiki/%D0%98%D1%81%D0%BF%D0%BE%D0%BB%D1%8C%D0%B7%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5-%D1%88%D0%B0%D0%B1%D0%BB%D0%BE%D0%BD%D0%BE%D0%B2-%D0%B2-%D1%81%D0%B8%D1%81%D1%82%D0%B5%D0%BC%D0%BD%D0%BE%D0%BC-%D0%BF%D1%80%D0%BE%D0%BC%D0%BF%D1%82%D0%B5"  # noqa: E501

ATTR_FILENAME = "file_name"
ATTR_SEED = "seed"
ATTR_PROMPT = "prompt"
