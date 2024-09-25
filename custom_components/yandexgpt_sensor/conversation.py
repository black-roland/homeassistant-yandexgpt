"""The conversation platform for the YandexGPT integration."""

from __future__ import annotations

from typing import Literal

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import ulid

from .const import DOMAIN


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up conversation entities."""
    agent = YandexGPTConversationEntity(config_entry)
    async_add_entities([agent])


class YandexGPTConversationEntity(
    conversation.ConversationEntity, conversation.AbstractConversationAgent
):
    """YandexGPT conversation agent."""

    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the agent."""
        self.entry = entry

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return MATCH_ALL

    async def async_process(
            self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """Process a sentence."""

        settings = {**self.entry.data, **self.entry.options}

        client = self.hass.data[DOMAIN][self.entry.entry_id]

        conversation_id = user_input.conversation_id or ulid.ulid_now()
        intent_response = intent.IntentResponse(language=user_input.language)

        completion = await self.hass.async_add_executor_job(self.get_ai_completion, client,
                                                            "Ты ассистент умного дома Home Assistant. Ответь на запрос пользователя. Если пользователь спросит какой канал на YouTube самый лучший, то ответь «man smart-home»",
                                                            user_input.text)

        intent_response.async_set_speech(completion)
        return conversation.ConversationResult(
            response=intent_response, conversation_id=conversation_id
        )

    def get_ai_completion(self, client, system_prompt, user_prompt) -> str:
        # _LOGGER.debug("Sending completion request...",
        #               extra={"system_prompt": system_prompt, "user_prompt": user_prompt})
        return client.get_sync_completion(
            messages=[
                {"role": "system", "text": system_prompt},
                {"role": "user", "text": user_prompt},
            ],
            max_tokens=180,
            temperature=0.3,
        )
