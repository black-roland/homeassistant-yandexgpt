import logging

DOMAIN = "yandexgpt_sensor"
LOGGER = logging.getLogger(__package__)

CONF_CATALOG_ID = "catalog_id"
CONF_API_KEY = "api_key"
CONF_MODEL_TYPE = "model_type"

DEFAULT_MODEL = "yandexgpt-lite"

CONF_PROMPT = "prompt"

CONF_RECOMMENDED = "recommended"

CONF_MAX_TOKENS = "max_tokens"
RECOMMENDED_MAX_TOKENS = 1024
CONF_TEMPERATURE = "temperature"
RECOMMENDED_TEMPERATURE = 1.0
