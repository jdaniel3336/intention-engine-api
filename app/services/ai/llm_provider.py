import json
from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

from app.core.config import Settings, get_settings

T = TypeVar("T", bound=BaseModel)


class LLMMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class LLMProvider(ABC):
    """Provider-agnostic interface for getting a structured response out of an LLM.

    Implementations are responsible for using whatever provider-native
    mechanism produces reliable structured output (tool use / function
    calling / JSON schema mode) and returning it parsed into
    ``response_schema``. Callers never see raw provider payloads.
    """

    @abstractmethod
    def generate(
        self,
        messages: list[LLMMessage],
        response_schema: type[T],
        system: str | None = None,
    ) -> T:
        raise NotImplementedError


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def generate(
        self,
        messages: list[LLMMessage],
        response_schema: type[T],
        system: str | None = None,
    ) -> T:
        tool_name = "emit_result"
        tool = {
            "name": tool_name,
            "description": f"Emit the result matching the {response_schema.__name__} schema.",
            "input_schema": response_schema.model_json_schema(),
        }
        response = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=system or "",
            messages=[{"role": m.role, "content": m.content} for m in messages],
            tools=[tool],
            tool_choice={"type": "tool", "name": tool_name},
        )
        for block in response.content:
            if block.type == "tool_use" and block.name == tool_name:
                return response_schema.model_validate(block.input)
        raise RuntimeError("Anthropic response did not include the expected tool_use block")


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def generate(
        self,
        messages: list[LLMMessage],
        response_schema: type[T],
        system: str | None = None,
    ) -> T:
        chat_messages = []
        if system:
            chat_messages.append({"role": "system", "content": system})
        chat_messages.extend({"role": m.role, "content": m.content} for m in messages)

        response = self._client.chat.completions.create(
            model=self._model,
            messages=chat_messages,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": response_schema.__name__,
                    "schema": response_schema.model_json_schema(),
                    "strict": False,
                },
            },
        )
        content = response.choices[0].message.content
        return response_schema.model_validate(json.loads(content))


_DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-5",
    "openai": "gpt-4o",
}


def build_llm_provider(settings: Settings) -> LLMProvider:
    provider = settings.llm_provider.lower()
    model = settings.llm_model or _DEFAULT_MODELS.get(provider, "")

    if provider == "anthropic":
        return AnthropicProvider(api_key=settings.llm_api_key, model=model)
    if provider == "openai":
        return OpenAIProvider(api_key=settings.llm_api_key, model=model)
    raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider!r}")


def get_llm_provider() -> LLMProvider:
    return build_llm_provider(get_settings())
