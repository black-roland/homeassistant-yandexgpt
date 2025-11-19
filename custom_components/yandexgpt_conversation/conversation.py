"""The conversation platform for the YandexGPT integration."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Literal

from grpc.aio import AioRpcError
from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LLM_HASS_API, MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import intent
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from yandex_cloud_ml_sdk import AsyncYCloudML
from yandex_cloud_ml_sdk._models.completions.message import TextMessage
from yandex_cloud_ml_sdk._models.completions.result import (AlternativeStatus,
                                                            GPTModelResult)

from .const import (CONF_ASYNCHRONOUS_MODE, CONF_CHAT_MODEL, CONF_MAX_TOKENS,
                    CONF_MODEL_VERSION, CONF_PROMPT, CONF_TEMPERATURE,
                    DEFAULT_CHAT_MODEL, DEFAULT_INSTRUCTIONS_PROMPT_RU,
                    DEFAULT_MODEL_VERSION, DOMAIN, LOGGER,
                    RECOMMENDED_MAX_TOKENS, RECOMMENDED_TEMPERATURE)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up conversation entities."""
    agent = YandexGPTConversationEntity(config_entry)
    async_add_entities([agent])


def _convert_content(chat_content: conversation.Content) -> TextMessage:
    if isinstance(chat_content, conversation.ToolResultContent):
        raise TypeError(f"Unexpected content type: {type(chat_content)}")

    return TextMessage(role=chat_content.role, text=str(chat_content.content))


async def _transform_stream(
    stream: AsyncGenerator[GPTModelResult, None],
) -> AsyncGenerator[conversation.AssistantContentDeltaDict, None]:
    """Transform YandexGPT stream into HA format."""

    streamed_text = ""
    prev_text = ""
    async for curr_chunk in stream:
        LOGGER.debug("Received partial result: %s", curr_chunk)

        alt = curr_chunk.alternatives[0]
        text, status = alt.text, alt.status

        if status in (AlternativeStatus.FINAL, AlternativeStatus.TRUNCATED_FINAL):
            if status == AlternativeStatus.TRUNCATED_FINAL:
                LOGGER.warning("Response was truncated by YandexGPT")
            delta = text[len(streamed_text):]
            yield {"content": delta}
            # In case a new message appears after this on is finalized
            prev_text = ""
            streamed_text = ""
            continue

        if status == AlternativeStatus.CONTENT_FILTER:
            LOGGER.warning("The message got blocked by the ethics filter")
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="ethics_filter",
            )

        # First chunk - just store and send role
        if prev_text == "":
            yield {"role": "assistant"}
            prev_text = text
            continue

        if status != AlternativeStatus.PARTIAL:
            continue

        # Chunks are shifted by 1: extract a substring from the current
        # chunk using the length of the previous chunk.
        #
        # This is a workaround to avoid issues with emojis and other 4-byte
        # characters. In streaming mode, LLM-generated text could be split
        # mid-character, breaking 4-byte sequences:
        # https://github.com/black-roland/homeassistant-yandexgpt/issues/17
        delta = text[len(streamed_text): len(prev_text)]
        yield {"content": delta}
        streamed_text = prev_text
        prev_text = text


class YandexGPTConversationEntity(
    conversation.ConversationEntity, conversation.AbstractConversationAgent
):
    """YandexGPT conversation agent."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the agent."""
        self.entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Yandex",
            model="YandexGPT",
            entry_type=dr.DeviceEntryType.SERVICE,
        )
        if self.entry.options.get(CONF_LLM_HASS_API):
            self._attr_supported_features = (
                conversation.ConversationEntityFeature.CONTROL
            )

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return MATCH_ALL

    async def _async_handle_message(
        self,
        user_input: conversation.ConversationInput,
        chat_log: conversation.ChatLog,
    ) -> conversation.ConversationResult:
        """Process a conversation with YandexGPT."""
        settings = {**self.entry.data, **self.entry.options}

        try:
            await chat_log.async_provide_llm_data(
                user_input.as_llm_context(DOMAIN),
                None,
                settings.get(CONF_PROMPT, DEFAULT_INSTRUCTIONS_PROMPT_RU),
                user_input.extra_system_prompt,
            )
        except conversation.ConverseError as err:
            return err.as_conversation_result()

        client: AsyncYCloudML = self.entry.runtime_data
        model_name = settings.get(CONF_CHAT_MODEL, DEFAULT_CHAT_MODEL).split("/")[0]
        model_ver = settings.get(CONF_MODEL_VERSION, DEFAULT_MODEL_VERSION)
        model_conf = {
            "temperature": settings.get(CONF_TEMPERATURE, RECOMMENDED_TEMPERATURE),
            "max_tokens": settings.get(CONF_MAX_TOKENS, RECOMMENDED_MAX_TOKENS),
        }

        messages: list[TextMessage] = [
            _convert_content(content) for content in chat_log.content
        ]

        LOGGER.debug("Prompt: %s", messages)

        try:
            model = client.models.completions(model_name, model_version=model_ver)
            configured_model = model.configure(**model_conf)

            if settings.get(CONF_ASYNCHRONOUS_MODE, False):
                operation = await configured_model.run_deferred(messages)
                LOGGER.debug("Async operation ID: %s", operation.id)
                result = await operation.wait(poll_timeout=300, poll_interval=0.5)

                # Convert single result to stream format
                async def single_result_stream():
                    yield result

                response_stream = single_result_stream()
            else:
                response_stream = configured_model.run_stream(messages)

            async for content in chat_log.async_add_delta_content_stream(
                user_input.agent_id,
                _transform_stream(response_stream),
            ):
                if isinstance(content, conversation.AssistantContent):
                    messages.append(_convert_content(content))
        except AioRpcError as err:
            LOGGER.exception("Error talking to Yandex Cloud: %s", err)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="yandex_cloud_error",
                translation_placeholders={"details": str(err.details())},
            ) from err

        intent_response = intent.IntentResponse(language=user_input.language)
        assert type(chat_log.content[-1]) is conversation.AssistantContent
        intent_response.async_set_speech(chat_log.content[-1].content or "")
        return conversation.ConversationResult(
            response=intent_response,
            conversation_id=chat_log.conversation_id,
            continue_conversation=chat_log.continue_conversation,
        )

    async def _async_entry_update_listener(
        self, hass: HomeAssistant, entry: ConfigEntry
    ) -> None:
        """Handle options update."""
        await hass.config_entries.async_reload(entry.entry_id)
