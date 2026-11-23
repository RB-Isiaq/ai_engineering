"""
One interface over several LLM providers.

OpenAI, Gemini and Ollama all expose an OpenAI-compatible Chat Completions endpoint,
so a single client library works for every one of them - only the base URL, API key
and model name change.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from dataclasses import dataclass, field
from functools import cache

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)

Message = dict[str, str]


@dataclass(frozen=True)
class Provider:
    name: str
    default_model: str
    base_url: str | None = None
    key_env: str | None = None
    # Extra kwargs sent with every request (e.g. OpenAI-only parameters)
    request_defaults: dict = field(default_factory=dict)


def _ollama_url() -> str:
    url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    return url if url.endswith("/v1") else f"{url}/v1"


PROVIDERS: dict[str, Provider] = {
    "openai": Provider(
        name="openai",
        default_model="gpt-6-luna",
        key_env="OPENAI_API_KEY",
        request_defaults={"reasoning_effort": "none"},
    ),
    "anthropic": Provider(
        name="anthropic",
        default_model="claude-haiku-5-5",
        base_url="https://api.anthropic.com/v1/",
        key_env="ANTHROPIC_API_KEY",
    ),
    "gemini": Provider(
        name="gemini",
        default_model="gemini-3.1-flash-lite",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        key_env="GOOGLE_API_KEY",
    ),
    "groq": Provider(
        name="groq",
        default_model="openai/gpt-oss-120b",
        base_url="https://api.groq.com/openai/v1",
        key_env="GROQ_API_KEY",
    ),
    "openrouter": Provider(
        name="openrouter",
        default_model="openai/gpt-oss-120b",
        base_url="https://openrouter.ai/api/v1",
        key_env="OPENROUTER_API_KEY",
    ),
    "ollama": Provider(
        name="ollama",
        default_model="llama3.2",
        base_url=_ollama_url(),
        key_env="OLLAMA_API_KEY",
    ),
}

DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")


def _provider(name: str | None) -> Provider:
    name = name or DEFAULT_PROVIDER
    if name not in PROVIDERS:
        raise ValueError(f"Unknown provider {name!r}; choose from {sorted(PROVIDERS)}")
    return PROVIDERS[name]


@cache
def get_client(provider: str | None = None) -> OpenAI:
    """Return a (cached) OpenAI-compatible client for the given provider."""
    p = _provider(provider)
    api_key = os.getenv(p.key_env) if p.key_env else None
    if p.name == "ollama":
        api_key = api_key or "ollama"  # local Ollama ignores the key, but the SDK needs one
    elif not api_key:
        raise RuntimeError(f"{p.key_env} is not set - add it to your .env file")
    return OpenAI(base_url=p.base_url, api_key=api_key)


def available_providers() -> list[str]:
    """Providers usable right now: Ollama plus any whose API key is set."""
    return [
        name
        for name, p in PROVIDERS.items()
        if name == "ollama" or (p.key_env and os.getenv(p.key_env))
    ]


def completion(messages: list, provider: str | None = None, model: str | None = None, **kwargs):
    """Raw SDK call - returns the full response object (needed for tool calls, usage, etc.)."""
    p = _provider(provider)
    params = {**p.request_defaults, **kwargs}
    return get_client(p.name).chat.completions.create(
        model=model or p.default_model, messages=messages, **params
    )


def chat(
    messages: list[Message],
    provider: str | None = None,
    model: str | None = None,
    as_json: bool = False,
    **kwargs,
) -> str | dict:
    """Send a full message list and return the reply (parsed if as_json=True)."""
    if as_json:
        kwargs["response_format"] = {"type": "json_object"}
    reply = completion(messages, provider, model, **kwargs).choices[0].message.content or ""
    return json.loads(reply) if as_json else reply


def ask(prompt: str, system: str | None = None, **kwargs) -> str | dict:
    """Single-turn convenience wrapper around chat()."""
    messages = [{"role": "system", "content": system}] if system else []
    messages.append({"role": "user", "content": prompt})
    return chat(messages, **kwargs)


def stream(
    messages: list[Message], provider: str | None = None, model: str | None = None, **kwargs
) -> Iterator[str]:
    """Yield the reply chunk by chunk as the model generates it."""
    for chunk in completion(messages, provider, model, stream=True, **kwargs):
        if chunk.choices and (delta := chunk.choices[0].delta.content):
            yield delta


class Conversation:
    """
    LLMs are stateless - "memory" is just resending the history every turn.
    This class keeps that history for you.
    """

    def __init__(self, system: str, provider: str | None = None, model: str | None = None):
        self.provider, self.model = provider, model
        self.messages: list[Message] = [{"role": "system", "content": system}]

    def say(self, text: str) -> str:
        self.messages.append({"role": "user", "content": text})
        reply = chat(self.messages, provider=self.provider, model=self.model)
        self.messages.append({"role": "assistant", "content": reply})
        return reply

    def reset(self) -> None:
        del self.messages[1:]
