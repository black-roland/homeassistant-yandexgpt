"""The conversation platform for the YandexGPT integration."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from typing import Literal, Callable, Any

from homeassistant.components import conversation
from homeassistant.components.conversation import trace
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL, CONF_LLM_HASS_API
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, TemplateError
from homeassistant.helpers import intent, llm
from homeassistant.helpers import template
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import ulid

from .const import DOMAIN, LOGGER, CONF_PROMPT, CONF_TEMPERATURE, RECOMMENDED_TEMPERATURE, CONF_MAX_TOKENS, \
    RECOMMENDED_MAX_TOKENS

# Max number of back and forth with the LLM to generate a response
MAX_TOOL_ITERATIONS = 10


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
        # FIXME: user YandexGPTMessage type instead of string
        self.history: dict[str, list[str]] = {}
        if self.entry.options.get(CONF_LLM_HASS_API):
            self._attr_supported_features = (
                conversation.ConversationEntityFeature.CONTROL
            )

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return MATCH_ALL

    async def async_process(
            self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """Process a sentence."""
        settings = {**self.entry.data, **self.entry.options}

        options = self.entry.options
        intent_response = intent.IntentResponse(language=user_input.language)
        llm_api: llm.APIInstance | None = None
        user_name: str | None = None
        llm_context = llm.LLMContext(
            platform=DOMAIN,
            context=user_input.context,
            user_prompt=user_input.text,
            language=user_input.language,
            assistant=conversation.DOMAIN,
            device_id=user_input.device_id,
        )

        if settings.get(CONF_LLM_HASS_API):
            try:
                llm_api = await llm.async_get_api(
                    self.hass,
                    settings[CONF_LLM_HASS_API],
                    llm_context,
                )
            except HomeAssistantError as err:
                LOGGER.error("Error getting LLM API: %s", err)
                intent_response.async_set_error(
                    intent.IntentResponseErrorCode.UNKNOWN,
                    f"Error preparing LLM API: {err}",
                )
                return conversation.ConversationResult(
                    response=intent_response, conversation_id=user_input.conversation_id
                )

        if user_input.conversation_id is None:
            conversation_id = ulid.ulid_now()
            messages = []

        elif user_input.conversation_id in self.history:
            conversation_id = user_input.conversation_id
            messages = self.history[conversation_id]

        else:
            # Conversation IDs are ULIDs. We generate a new one if not provided.
            # If an old OLID is passed in, we will generate a new one to indicate
            # a new conversation was started. If the user picks their own, they
            # want to track a conversation and we respect it.
            try:
                ulid.ulid_to_bytes(user_input.conversation_id)
                conversation_id = ulid.ulid_now()
            except ValueError:
                conversation_id = user_input.conversation_id

            messages = []

        if (
                user_input.context
                and user_input.context.user_id
                and (
                user := await self.hass.auth.async_get_user(user_input.context.user_id)
        )
        ):
            user_name = user.name

        try:
            # FIXME: Replace BASE_PROMPT and DEFAULT_INSTRUCTIONS_PROMPT with Russian alternatives
            prompt_parts = [
                template.Template(
                    llm.BASE_PROMPT
                    + options.get(CONF_PROMPT, llm.DEFAULT_INSTRUCTIONS_PROMPT),
                    self.hass,
                ).async_render(
                    {
                        "ha_name": self.hass.config.location_name,
                        "user_name": user_name,
                        "llm_context": llm_context,
                    },
                    parse_result=False,
                )
            ]

        except TemplateError as err:
            LOGGER.error("Error rendering prompt: %s", err)
            intent_response.async_set_error(
                intent.IntentResponseErrorCode.UNKNOWN,
                f"Sorry, I had a problem with my template: {err}",
            )
            return conversation.ConversationResult(
                response=intent_response, conversation_id=conversation_id
            )

        if llm_api:
            LOGGER.debug(llm_api.api_prompt)
            prompt_parts.append(llm_api.api_prompt)

        prompt = "\n".join(prompt_parts)

        messages = [*messages, user_input.text]

        LOGGER.debug("Prompt: %s", messages)
        trace.async_conversation_trace_append(
            trace.ConversationTraceEventType.AGENT_DETAIL,
            {"system": prompt, "messages": messages},
        )

        client = self.hass.data[DOMAIN][self.entry.entry_id]

        # To prevent infinite loops, we limit the number of iterations
        try:
            response = await self.hass.async_add_executor_job(
                client.get_sync_completion,
                [
                    {"role": "system", "text": prompt},
                ] + list(map(lambda message: {"role": "user",
                                              "text": message},
                             messages)),
                options.get(CONF_TEMPERATURE,
                            RECOMMENDED_TEMPERATURE),
                options.get(CONF_MAX_TOKENS, RECOMMENDED_MAX_TOKENS),
            )
        except Exception as err:
            LOGGER.exception(err)

            intent_response.async_set_error(
                intent.IntentResponseErrorCode.UNKNOWN,
                f"Sorry, I had a problem talking to YandexGPT: {err}",
            )
            return conversation.ConversationResult(
                response=intent_response, conversation_id=conversation_id
            )

        LOGGER.debug("Response %s", response)

        messages.append(response)

        self.history[conversation_id] = messages

        # Create intent response
        intent_response.async_set_speech(response)
        return conversation.ConversationResult(
            response=intent_response, conversation_id=conversation_id
        )