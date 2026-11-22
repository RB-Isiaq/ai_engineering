"""Jupyter-only display helpers."""

from collections.abc import Iterable

from IPython.display import Markdown, display, update_display


def show(markdown: str) -> None:
    display(Markdown(markdown))


def show_stream(chunks: Iterable[str]) -> str:
    """Render streamed chunks as live-updating markdown; returns the full text."""
    text = ""
    handle = display(Markdown(""), display_id=True)
    for chunk in chunks:
        text += chunk
        update_display(Markdown(text), display_id=handle.display_id)
    return text
