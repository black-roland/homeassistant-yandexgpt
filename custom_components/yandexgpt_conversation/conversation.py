"""The conversation platform for the YandexGPT integration."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from typing import Literal

from grpc.aio import AioRpcError
from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LLM_HASS_API, MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, TemplateError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import intent, template
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from yandex_cloud_ml_sdk import AsyncYCloudML
from yandex_cloud_ml_sdk._models.completions.message import \
    CompletionsMessageType

from .const import (CONF_ASYNCHRONOUS_MODE, CONF_CHAT_MODEL, CONF_MAX_TOKENS,
                    CONF_MAX_TOOL_ITERATIONS, CONF_MODEL_VERSION,
                    CONF_NO_HA_DEFAULT_PROMPT, CONF_PROMPT, CONF_TEMPERATURE,
                    DEFAULT_CHAT_MODEL, DEFAULT_INSTRUCTIONS_PROMPT_RU,
                    DEFAULT_MAX_TOOL_ITERATIONS, DEFAULT_MODEL_VERSION,
                    DEFAULT_NO_HA_DEFAULT_PROMPT, DOMAIN, LOGGER,
                    RECOMMENDED_MAX_TOKENS, RECOMMENDED_TEMPERATURE)
from .mappers import ContentConverter, StreamTransformer


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up conversation entities."""
    agent = YandexGPTConversationEntity(config_entry)
    async_add_entities([agent])


class YandexGPTConversationEntity(
    conversation.ConversationEntity, conversation.AbstractConversationAgent  # type: ignore
):
    """YandexGPT conversation agent."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supports_streaming = True

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

        system_prompt = settings.get(CONF_PROMPT, DEFAULT_INSTRUCTIONS_PROMPT_RU)

        try:
            await chat_log.async_provide_llm_data(
                user_input.as_llm_context(DOMAIN),
                settings.get(CONF_LLM_HASS_API),
                system_prompt,
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

        no_ha_default_prompt = settings.get(CONF_NO_HA_DEFAULT_PROMPT, DEFAULT_NO_HA_DEFAULT_PROMPT)
        system_prompt_override = await self._async_expand_prompt_template(
            system_prompt, user_input) if no_ha_default_prompt else None

        content_converter = ContentConverter(system_prompt_override=system_prompt_override)
        messages: list[CompletionsMessageType] = content_converter.to_yandexgpt_api(chat_log.content)

        if chat_log.llm_api:
            model_conf["tools"] = [
                ContentConverter.format_tool(tool, chat_log.llm_api.custom_serializer)
                for tool in chat_log.llm_api.tools
            ]

        try:
            model = client.models.completions(model_name, model_version=model_ver)
            configured_model = model.configure(**model_conf)

            max_tool_iterations = settings.get(CONF_MAX_TOOL_ITERATIONS, DEFAULT_MAX_TOOL_ITERATIONS)
            for _iteration in range(max_tool_iterations):
                LOGGER.debug("Prompt: %s", messages)

                if settings.get(CONF_ASYNCHRONOUS_MODE, False):
                    operation = await configured_model.run_deferred(messages)
                    LOGGER.debug("Async operation ID: %s", operation.id)
                    result = await operation.wait(poll_timeout=300, poll_interval=0.5)

                    async def single_result_stream():
                        yield result

                    response_stream = single_result_stream()
                else:
                    response_stream = configured_model.run_stream(messages)

                stream_transformer = StreamTransformer(response_stream)
                content_converter = ContentConverter(
                    stream_transformer=stream_transformer, system_prompt_override=system_prompt_override)

                messages.extend(
                    content_converter.to_yandexgpt_api(
                        [
                            content
                            async for content in chat_log.async_add_delta_content_stream(
                                user_input.agent_id,
                                stream_transformer.to_chatlog_api(),
                            )
                        ]
                    )
                )

                if not chat_log.unresponded_tool_results:
                    break
        except AioRpcError as err:
            LOGGER.exception("Error talking to Yandex Cloud: %s", err)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="yandex_cloud_error",
                translation_placeholders={"details": str(err.details())},
            ) from err
        except TimeoutError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="yandex_cloud_error",
                translation_placeholders={"details": "Async operation timed out"},
            ) from err

        intent_response = intent.IntentResponse(language=user_input.language)
        assert type(chat_log.content[-1]) is conversation.AssistantContent
        intent_response.async_set_speech(chat_log.content[-1].content or "")
        return conversation.ConversationResult(
            response=intent_response,
            conversation_id=chat_log.conversation_id,
            continue_conversation=chat_log.continue_conversation,
        )

    async def _async_expand_prompt_template(
        self, prompt_template: str, user_input: conversation.ConversationInput
    ) -> str:
        """Render the prompt template."""
        try:
            system_prompt = template.Template(prompt_template, self.hass).async_render(parse_result=False)

            if user_input.extra_system_prompt:
                system_prompt += user_input.extra_system_prompt

            return system_prompt
        except TemplateError as err:
            raise HomeAssistantError("Error rendering prompt template") from err

    async def _async_entry_update_listener(
        self, hass: HomeAssistant, entry: ConfigEntry
    ) -> None:
        """Handle options update."""
        await hass.config_entries.async_reload(entry.entry_id)
