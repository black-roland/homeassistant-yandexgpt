"""Mappers for converting between YandexGPT and Home Assistant message formats."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import json
from collections.abc import AsyncGenerator, AsyncIterator, Callable
from typing import Any, Iterable, Optional, cast

from homeassistant.components import conversation
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import llm
from voluptuous_openapi import convert
from yandex_cloud_ml_sdk._models.completions.message import \
    CompletionsMessageType
from yandex_cloud_ml_sdk._models.completions.message import \
    FunctionResultMessageDict as ToolResultsMessageType
from yandex_cloud_ml_sdk._models.completions.result import (AlternativeStatus,
                                                            GPTModelResult)
from yandex_cloud_ml_sdk._tools.tool import FunctionTool
from yandex_cloud_ml_sdk._tools.tool_call import AsyncToolCall

from .const import DOMAIN, LOGGER


class StreamTransformer:

    def __init__(self, stream: AsyncIterator[GPTModelResult[AsyncToolCall]]) -> None:
        self.stream = stream
        self._tool_calls_event = None

    @property
    def tool_calls_message(self) -> GPTModelResult[AsyncToolCall]:
        assert self._tool_calls_event
        return self._tool_calls_event

    async def to_chatlog_api(
        self,
    ) -> AsyncGenerator[conversation.AssistantContentDeltaDict, None]:
        """Transform YandexGPT stream into HA format."""

        streamed_text = ""
        prev_text = ""
        async for event in self.stream:
            LOGGER.debug("Received partial result: %s", event)

            alt = event.alternatives[0]
            text, status = alt.text, alt.status

            if status in (AlternativeStatus.FINAL, AlternativeStatus.TRUNCATED_FINAL):
                if status == AlternativeStatus.TRUNCATED_FINAL:
                    LOGGER.warning("Response was truncated by YandexGPT")
                delta = text[len(streamed_text):]
                yield {"content": delta}
                # Reset for potential new messages
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
                        # Broken typings in ML SDK?
                        tool_name=tool_call.function.name,  # type: ignore
                        tool_args=tool_call.function.arguments,  # type: ignore
                    )
                    for tool_call in alt.tool_calls
                ]
                yield {"tool_calls": tool_calls}
                # Save the original event as-is.
                # Later it's prepended before the tool results message.
                self._tool_calls_event = event
                continue

            # First chunk - just store and send role
            if prev_text == "":
                yield {"role": "assistant"}
                prev_text = text
                continue

            if status != AlternativeStatus.PARTIAL:
                continue

            # Calculate delta between adjacent chunks to handle multi-byte characters.
            # Workaround for emoji/4-byte character streaming issues:
            # https://github.com/black-roland/homeassistant-yandexgpt/issues/17
            delta = text[len(streamed_text): len(prev_text)]
            yield {"content": delta}
            streamed_text = prev_text
            prev_text = text


class ContentConverter:

    def __init__(
        self, stream_transformer: Optional[StreamTransformer] = None, system_prompt_override: Optional[str] = None
    ) -> None:
        self._stream_transformer = stream_transformer
        self._system_prompt_override = system_prompt_override

    def to_yandexgpt_api(
        self, chat_logs: Iterable[conversation.Content]
    ) -> list[CompletionsMessageType]:
        """Convert Home Assistant conversation content to YandexGPT message format."""
        messages: list[CompletionsMessageType] = []

        for content in chat_logs:
            if isinstance(content, conversation.ToolResultContent):
                # Group tool results into a single message
                previous = cast(ToolResultsMessageType, messages[-1])
                if "tool_results" in previous and isinstance(previous["tool_results"], list):
                    previous["tool_results"].append({
                        "name": content.tool_name,
                        "content": json.dumps(content.tool_result),
                    })
                    continue

                messages.append({
                    "role": "assistant",
                    "tool_results": [{
                        "name": content.tool_name,
                        "content": json.dumps(content.tool_result),
                    }],
                })

            elif isinstance(content, conversation.AssistantContent) and content.tool_calls:
                if not self._stream_transformer:
                    continue

                # ML SDK doesn't provide a convenient way to reconstruct
                # a tool calls object from chat logs so the original message
                # is saved temporary during YandexGPT -> ChatLog API transform.
                messages.append(self._stream_transformer.tool_calls_message)

            elif isinstance(content, conversation.SystemContent) and self._system_prompt_override:
                messages.append({"role": "system", "text": self._system_prompt_override})

            elif content.content:
                messages.append({"role": content.role, "text": content.content})

            else:
                raise TypeError(f"Unexpected content type: {type(content)}")

        return messages

    @staticmethod
    def format_tool(
        tool: llm.Tool, custom_serializer: Callable[[Any], Any] | None
    ) -> FunctionTool:
        """Convert HA tool to YandexGPT format."""
        # client.tools.function seems to have broken typings,
        # use FunctionTool directly
        return FunctionTool(
            name=tool.name,
            description=tool.description,
            parameters=convert(
                tool.parameters, custom_serializer=custom_serializer),
        )
