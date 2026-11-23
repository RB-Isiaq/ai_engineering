"""Glue between Gradio chat components and the Chat Completions message format."""

from __future__ import annotations


def history_to_messages(history: list[dict]) -> list[dict]:
    """
    Gradio's `type="messages"` history carries extra keys (metadata, options) and may contain
    non-text content (files, components). Keep only plain role/content text turns.
    """
    return [
        {"role": h["role"], "content": h["content"]}
        for h in history
        if h.get("role") in ("user", "assistant") and isinstance(h.get("content"), str)
    ]


def build_messages(system: str, history: list[dict], message: str | None = None) -> list[dict]:
    messages = [{"role": "system", "content": system}, *history_to_messages(history)]
    if message is not None:
        messages.append({"role": "user", "content": message})
    return messages


def accumulate(chunks):
    """Gradio streams by re-rendering the full text, so yield the running total."""
    text = ""
    for chunk in chunks:
        text += chunk
        yield text
