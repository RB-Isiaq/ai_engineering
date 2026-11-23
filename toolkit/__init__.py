"""Small shared helpers reused across modules: LLM clients, tools, web scraping, UI glue."""

from toolkit.llm import (
    PROVIDERS,
    Conversation,
    ask,
    available_providers,
    chat,
    completion,
    get_client,
    stream,
)
from toolkit.tools import Tool, ToolBox, ToolCall
from toolkit.web import Page, fetch_page

__all__ = [
    "PROVIDERS",
    "Conversation",
    "Page",
    "Tool",
    "ToolBox",
    "ToolCall",
    "ask",
    "available_providers",
    "chat",
    "completion",
    "fetch_page",
    "get_client",
    "stream",
]
