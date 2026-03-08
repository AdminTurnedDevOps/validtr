"""Google Gemini provider."""

import json
import logging

from google import genai
from google.genai import types

from providers.base import CompletionResponse, LLMProvider, Message, ToolDefinition

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """Provider for Google Gemini models."""

    @property
    def default_model(self) -> str:
        return "gemini-2.5-flash"

    @property
    def provider_name(self) -> str:
        return "gemini"

    def __init__(self, api_key: str, model: str | None = None):
        super().__init__(api_key, model)
        self.client = genai.Client(api_key=api_key)

    def _convert_messages(self, messages: list[Message]) -> tuple[str | None, list[types.Content]]:
        """Convert messages to Gemini format. Returns (system_instruction, contents)."""
        system = None
        contents: list[types.Content] = []

        for msg in messages:
            if msg.role == "system":
                system = msg.content
            elif msg.role == "user":
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=msg.content)],
                ))
            elif msg.role == "assistant":
                parts = []
                if msg.content:
                    parts.append(types.Part.from_text(text=msg.content))
                if msg.tool_calls:
                    for tc in msg.tool_calls:
                        parts.append(types.Part.from_function_call(
                            name=tc["name"],
                            args=tc["arguments"],
                        ))
                contents.append(types.Content(role="model", parts=parts))
            elif msg.role == "tool":
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_function_response(
                        name=msg.tool_call_id or "unknown",
                        response={"result": msg.content},
                    )],
                ))

        return system, contents

    def _convert_tools(self, tools: list[ToolDefinition]) -> list[types.Tool]:
        """Convert tools to Gemini format."""
        declarations = []
        for t in tools:
            declarations.append(types.FunctionDeclaration(
                name=t.name,
                description=t.description,
                parameters=t.parameters,
            ))
        return [types.Tool(function_declarations=declarations)]

    async def complete(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> CompletionResponse:
        system, contents = self._convert_messages(messages)

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        if system:
            config.system_instruction = system
        if tools:
            config.tools = self._convert_tools(tools)
        if json_mode:
            config.response_mime_type = "application/json"

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )
        except Exception as e:
            logger.error("Gemini API error: %s", e)
            raise

        content = ""
        tool_calls = []

        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if part.text:
                    content += part.text
                elif part.function_call:
                    fc = part.function_call
                    tool_calls.append({
                        "id": fc.name,
                        "name": fc.name,
                        "arguments": dict(fc.args) if fc.args else {},
                    })

        input_tokens = 0
        output_tokens = 0
        if response.usage_metadata:
            input_tokens = response.usage_metadata.prompt_token_count or 0
            output_tokens = response.usage_metadata.candidates_token_count or 0

        return CompletionResponse(
            content=content,
            tool_calls=tool_calls,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self.model,
            stop_reason="stop",
        )
