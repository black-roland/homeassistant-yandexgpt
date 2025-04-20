"""The conversation platform for the YandexGPT integration."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from collections.abc import AsyncGenerator, AsyncIterator, Callable
import json
from types import SimpleNamespace
from typing import Any, Iterable, Literal

from grpc.aio import AioRpcError
from homeassistant.components import assist_pipeline, conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LLM_HASS_API, MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr, intent, llm
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from yandex_cloud_ml_sdk import AsyncYCloudML
from yandex_cloud_ml_sdk._types.message import TextMessage
from yandex_cloud_ml_sdk._models.completions.result import (
    AlternativeStatus,
    GPTModelResult,
)
from yandex_cloud_ml_sdk._tools.tool import FunctionTool
from yandex_cloud_ml_sdk._tools.tool_call import AsyncToolCall
from yandex_cloud_ml_sdk._models.completions.message import (
    TextMessageWithToolCallsProtocol,
)
from voluptuous_openapi import convert
# from dataclasses import dataclass
# from yandex_cloud_ml_sdk._tools.tool_call_list import ToolCallList
# from yandex.cloud.ai.foundation_models.v1.text_common_pb2 import ToolCallList as ProtoCompletionsToolCallList

from .const import (
    CONF_ASYNCHRONOUS_MODE,
    CONF_CHAT_MODEL,
    CONF_MAX_TOKENS,
    CONF_MODEL_VERSION,
    CONF_PROMPT,
    CONF_TEMPERATURE,
    DEFAULT_CHAT_MODEL,
    DEFAULT_INSTRUCTIONS_PROMPT_RU,
    DEFAULT_MODEL_VERSION,
    DOMAIN,
    LOGGER,
    RECOMMENDED_MAX_TOKENS,
    RECOMMENDED_TEMPERATURE,
)

MAX_TOOL_ITERATIONS = 10


# @dataclass
# class TextMessageWithTools:
#     role: str
#     text: str
#     tool_calls: Any


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up conversation entities."""
    agent = YandexGPTConversationEntity(config_entry)
    async_add_entities([agent])


def _format_tool(
    tool: llm.Tool, custom_serializer: Callable[[Any], Any] | None
) -> FunctionTool:
    """Format tool specification."""
    # client.tools.function seems to have broken typings,
    # use FunctionTool directly
    return FunctionTool(
        name=tool.name,
        description=tool.description,
        parameters=convert(tool.parameters, custom_serializer=custom_serializer),
    )


def _convert_content(
    chat_content: Iterable[conversation.Content],
) -> list[TextMessage | dict[str, Any]]:
    """Convert Home Assistant conversation content to YandexGPT message format."""
    messages: list[TextMessage | dict[str, Any]] = []

    for content in chat_content:
        if isinstance(content, conversation.ToolResultContent):
            tool_results = {
                "role": "assistant",
                # FIXME: Grouping?
                # https://github.com/home-assistant/core/blob/2025.4.3/homeassistant/components/google_generative_ai_conversation/conversation.py#L341
                "tool_results": [
                    {
                        "name": content.tool_name,
                        "content": json.dumps(content.tool_result),
                    }
                ],
            }
            messages.append(tool_results)

        elif isinstance(content, conversation.AssistantContent):
            if content.content:
                messages.append(TextMessage(role="assistant", text=content.content))

            if content.tool_calls:
                # Tool calls are handled separately in _transform_stream
                # since SDK doesn't provide a way to create TextMessageWithToolCallsProtocol
                # tool_calls = {
                #     "role": "assistant",
                #     "tool_calls": {
                #         "_proto_origin": [
                #             {
                #                 "function_call": {
                #                     "name": tool_call.tool_name,
                #                     "arguments": tool_call.tool_args,
                #                 }
                #             }
                #             for tool_call in content.tool_calls
                #         ]
                #     },
                # }
                # messages.append(tool_calls)
                pass
        else:
            messages.append(
                TextMessage(role=content.role, text=str(content.content))
            )

    return messages


# def _convert_content(
#     chat_content: conversation.Content | conversation.ToolResultContent,
# ) -> TextMessage | dict[str, Any] | None:
#     """Convert Home Assistant conversation content to YandexGPT message format."""
#     if isinstance(chat_content, conversation.ToolResultContent):
#         return {
#             "role": "assistant",
#             # FIXME: Grouping?
#             # https://github.com/home-assistant/core/blob/2025.4.3/homeassistant/components/google_generative_ai_conversation/conversation.py#L341
#             "tool_results": [
#                 {
#                     "name": chat_content.tool_name,
#                     "content": json.dumps(chat_content.tool_result),
#                 }
#             ],
#         }

#     if (
#         isinstance(chat_content, conversation.AssistantContent)
#         and chat_content.tool_calls
#     ):
#         proto_tool_calls = ProtoCompletionsToolCallList(
#             tool_calls=[
#                 ProtoCompletionsToolCall(
#                     function_call=ProtoCompletionsFunctionCall(
#                         name=tool['name'],
#                         arguments=json.dumps(tool['arguments'])
#                     )
#                 )
#                 for tool in tool_calls
#             ]
#         )

#         # tool_calls: TextMessageWithToolCallsProtocol = TextMessageWithTools(
#         #     role="assistant",
#         #     text="",
#         #     tool_calls=Message(
#         #         tool_call_list=[
#         #             {
#         #                 "function_call": {
#         #                     "name": tool_call.tool_name,
#         #                     "arguments": tool_call.tool_args,
#         #                 }
#         #             }
#         #             for tool_call in chat_content.tool_calls
#         #         ]
#         #     ),
#         # )
#         # return tool_calls
#         # return {
#         #     "role": "assistant",
#         #     "tool_calls": {
#         #         "_proto_origin": [
#         #             {
#         #                 "function_call": {
#         #                     "name": tool_call.tool_name,
#         #                     "arguments": tool_call.tool_args,
#         #                 }
#         #             }
#         #             for tool_call in chat_content.tool_calls
#         #         ]
#         #     },
#         # }

#     return TextMessage(role=chat_content.role, text=str(chat_content.content))

# TODO: Fix typings
async def _transform_stream(
    stream: AsyncIterator[GPTModelResult[AsyncToolCall]],
    messages,
) -> AsyncGenerator[conversation.AssistantContentDeltaDict, None]:
    """Transform YandexGPT stream into HA format."""
    streamed_text = ""
    prev_text = ""
    async for event in stream:
        LOGGER.debug("Received partial result: %s", event)

        alt = event.alternatives[0]
        text, status = alt.text, alt.status

        if status in (AlternativeStatus.FINAL, AlternativeStatus.TRUNCATED_FINAL):
            if status == AlternativeStatus.TRUNCATED_FINAL:
                LOGGER.warning("Response was truncated by YandexGPT")
            delta = text[len(streamed_text) :]
            yield {"content": delta}
            # In case a new message appears after this one is finalized
            prev_text = ""
            streamed_text = ""
            continue

        if status == AlternativeStatus.CONTENT_FILTER:
            LOGGER.warning("The message got blocked by the ethics filter")
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="ethics_filter",
            )

        if status == AlternativeStatus.TOOL_CALLS and alt.tool_calls:
            tool_calls: list[llm.ToolInput] = [
                llm.ToolInput(
                    # Broken typings is SDK?
                    tool_name=tool_call.function.name,  # type: ignore[operator]
                    tool_args=tool_call.function.arguments,  # type: ignore[operator]
                )
                for tool_call in alt.tool_calls
            ]
            yield {"tool_calls": tool_calls}
            messages.append(event)
            continue

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
        delta = text[len(streamed_text) : len(prev_text)]
        yield {"content": delta}
        streamed_text = prev_text
        prev_text = text


class YandexGPTConversationEntity(
    conversation.ConversationEntity, conversation.AbstractConversationAgent  # type: ignore
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

    async def async_added_to_hass(self) -> None:
        """When entity is added to Home Assistant."""
        await super().async_added_to_hass()
        assist_pipeline.async_migrate_engine(
            self.hass, "conversation", self.entry.entry_id, self.entity_id
        )
        conversation.async_set_agent(self.hass, self.entry, self)
        self.entry.async_on_unload(
            self.entry.add_update_listener(self._async_entry_update_listener)
        )

    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from Home Assistant."""
        conversation.async_unset_agent(self.hass, self.entry)
        await super().async_will_remove_from_hass()

    async def _async_handle_message(
        self,
        user_input: conversation.ConversationInput,
        chat_log: conversation.ChatLog,
    ) -> conversation.ConversationResult:
        """Process a conversation with YandexGPT."""
        settings = {**self.entry.data, **self.entry.options}

        try:
            await chat_log.async_update_llm_data(
                DOMAIN,
                user_input,
                settings.get(CONF_LLM_HASS_API),
                settings.get(CONF_PROMPT, DEFAULT_INSTRUCTIONS_PROMPT_RU),
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

        # TODO: Fix typings
        # TODO: Fix 💩
        messages: list[TextMessage | dict[str, Any]] = _convert_content(chat_log.content)

        if chat_log.llm_api:
            model_conf["tools"] = [
                _format_tool(tool, chat_log.llm_api.custom_serializer)
                for tool in chat_log.llm_api.tools
            ]

        try:
            model = client.models.completions(model_name, model_version=model_ver)
            configured_model = model.configure(**model_conf)

            for _iteration in range(MAX_TOOL_ITERATIONS):
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

                messages.extend(
                    _convert_content(
                        [
                            content
                            async for content in chat_log.async_add_delta_content_stream(
                                user_input.agent_id, _transform_stream(response_stream, messages)
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
