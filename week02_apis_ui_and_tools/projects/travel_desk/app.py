"""
Harmattan Air travel desk: a tool-using booking assistant with a Gradio Blocks UI.

    uv run week02_apis_ui_and_tools/projects/travel_desk/app.py
"""

import json
from datetime import date

import gradio as gr
from db import init_db
from media import destination_art, speak
from tools import make_toolbox

from toolkit import ToolCall, available_providers
from toolkit.chat_ui import build_messages

SYSTEM = f"""You are the booking assistant for Harmattan Air, an airline flying from Lagos.
Today is {date.today():%A %d %B %Y}.

- Use the tools for every fare, booking and destination fact. Never guess prices.
- Before calling book_flight or cancel_booking, restate the details and get an explicit "yes".
- Ask for missing details (passenger name, date, cabin) one question at a time.
- Keep replies to two or three sentences. Quote prices in USD."""


def format_log(calls: list[ToolCall]) -> str:
    if not calls:
        return "_No tool calls yet._"
    return "\n\n".join(
        f"**{c.name}**(`{json.dumps(c.arguments)}`)\n```json\n{json.dumps(c.result, indent=1)}\n```"
        for c in calls
    )


def respond(history, provider, with_voice, with_art):
    calls: list[ToolCall] = []
    box = make_toolbox(on_call=calls.append)
    messages = build_messages(SYSTEM, history)

    history = history + [{"role": "assistant", "content": ""}]
    for chunk in box.stream(messages, provider=provider):
        history[-1]["content"] += chunk
        yield history, format_log(calls), gr.skip(), gr.skip()

    reply = history[-1]["content"]
    audio = speak(reply) if with_voice and reply else None
    cities = [c.result["city"] for c in calls if isinstance(c.result, dict) and "city" in c.result]
    image = destination_art(cities[-1]) if with_art and cities else gr.skip()
    yield history, format_log(calls), audio, image


def add_user_message(message, history):
    return "", history + [{"role": "user", "content": message}]


def build_ui() -> gr.Blocks:
    providers = available_providers()
    has_openai = "openai" in providers

    with gr.Blocks(title="Harmattan Air") as ui:
        gr.Markdown("## Harmattan Air · travel desk")
        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(type="messages", height=480)
                message = gr.Textbox(
                    placeholder="e.g. How much is business class to Nairobi?", show_label=False
                )
            with gr.Column(scale=2):
                image = gr.Image(height=260, interactive=False, show_label=False)
                audio = gr.Audio(autoplay=True, interactive=False, show_label=False)
                with gr.Accordion("Tool calls", open=True):
                    log = gr.Markdown("_No tool calls yet._")
        with gr.Row():
            provider = gr.Dropdown(providers, value=providers[0], label="Provider")
            with_voice = gr.Checkbox(label="Voice replies (OpenAI)", interactive=has_openai)
            with_art = gr.Checkbox(label="Destination art (OpenAI)", interactive=has_openai)

        message.submit(add_user_message, [message, chatbot], [message, chatbot]).then(
            respond, [chatbot, provider, with_voice, with_art], [chatbot, log, audio, image]
        )
    return ui


if __name__ == "__main__":
    init_db()
    build_ui().launch(inbrowser=True)
