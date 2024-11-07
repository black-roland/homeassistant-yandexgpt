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

RECOMMENDED_CHAT_MODEL = "yandexgpt/latest"
RECOMMENDED_MAX_TOKENS = 1024
RECOMMENDED_TEMPERATURE = 0.6

BASE_PROMPT_RU = (
    'Текущее время: {{ now().strftime("%H:%M:%S") }}. '
    'Текущая дата: {{ now().strftime("%Y-%m-%d") }}.\n'
)
DEFAULT_INSTRUCTIONS_PROMPT_RU = """Ты — голосовой ассистент для Home Assistant.
Отвечай на вопросы правдиво.
Отвечай простым текстом, без вводных фраз и объяснений. Не усложняй и отвечай по сути.
"""

ATTR_FILENAME = "file_name"
ATTR_SEED = "seed"
ATTR_PROMPT = "prompt"
