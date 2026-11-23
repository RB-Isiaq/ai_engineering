"""
Tech tutor with a chat UI: streaming answers, switchable provider and depth, and live
package lookups (PyPI / npm) so version questions aren't answered from stale training data.

    uv run week02_apis_ui_and_tools/projects/tutor_ui.py
"""

import gradio as gr
import requests

from toolkit import ToolBox, available_providers
from toolkit.chat_ui import accumulate, build_messages

DEPTH = {
    "Quick": "Answer in a few sentences plus a minimal code example if useful.",
    "Standard": "Explain what, why and a short example; mention one common pitfall.",
    "Deep dive": "Cover internals, trade-offs, alternatives and edge cases, with examples.",
}

SYSTEM = """You are a senior engineer answering a fellow developer's technical questions
(Python, JavaScript/TypeScript, web, LLM engineering). Be precise; skip basics they didn't ask for.
When a question depends on a package's current version, metadata or dependencies, call the
package lookup tools instead of relying on memory. Use markdown with fenced code blocks.
{depth}"""

box = ToolBox()


@box.tool
def pypi_package(name: str) -> dict:
    """Current metadata for a Python package from PyPI.

    Args:
        name: Package name, e.g. "httpx".
    """
    r = requests.get(f"https://pypi.org/pypi/{name}/json", timeout=10)
    if r.status_code == 404:
        return {"error": f"{name} not found on PyPI"}
    info = r.json()["info"]
    return {
        "name": info["name"],
        "latest_version": info["version"],
        "summary": info["summary"],
        "requires_python": info["requires_python"],
        "dependencies": (info.get("requires_dist") or [])[:15],
    }


@box.tool
def npm_package(name: str) -> dict:
    """Current metadata for a JavaScript package from the npm registry.

    Args:
        name: Package name, e.g. "zod" or "@tanstack/react-query".
    """
    r = requests.get(f"https://registry.npmjs.org/{name}/latest", timeout=10)
    if r.status_code == 404:
        return {"error": f"{name} not found on npm"}
    pkg = r.json()
    return {
        "name": pkg["name"],
        "latest_version": pkg["version"],
        "description": pkg.get("description"),
        "dependencies": sorted(pkg.get("dependencies", {}))[:15],
        "peer_dependencies": pkg.get("peerDependencies", {}),
    }


def respond(message, history, provider, depth):
    messages = build_messages(SYSTEM.format(depth=DEPTH[depth]), history, message)
    yield from accumulate(box.stream(messages, provider=provider))


def build_ui() -> gr.ChatInterface:
    providers = available_providers()
    return gr.ChatInterface(
        respond,
        type="messages",
        title="Tech tutor",
        additional_inputs=[
            gr.Dropdown(providers, value=providers[0], label="Provider"),
            gr.Radio(list(DEPTH), value="Standard", label="Depth"),
        ],
        additional_inputs_accordion=gr.Accordion("Settings", open=True),
        examples=[
            ["What's the latest version of FastAPI and what does it depend on?"],
            ["How do React Server Components differ from SSR?"],
            ["Why does `yield from` exist when I can loop and yield?"],
        ],
    )


if __name__ == "__main__":
    build_ui().launch(inbrowser=True)
