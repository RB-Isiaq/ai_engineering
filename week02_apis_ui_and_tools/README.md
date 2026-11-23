# week02_apis_ui_and_tools

This module goes from single API calls to interactive, tool-using applications. It compares how to
integrate frontier models: compatible endpoints, native SDKs, LiteLLM and OpenRouter. It covers the cost
levers that matter in production (reasoning effort, prompt caching), and how to build chat UIs with Gradio.
Most of it is about function calling: letting a model query and change real application state, safely,
with streaming. The two applications at the end use all of it.

## Notebooks

| Notebook | Scope |
|---|---|
| [01_provider_landscape](01_provider_landscape.ipynb) | Native SDKs vs compatible endpoints vs LiteLLM/OpenRouter, usage and cost reporting, reasoning effort, prompt caching |
| [02_model_panel](02_model_panel.ipynb) | N-party conversations with a shared-transcript pattern, mixed providers per participant |
| [03_gradio_interfaces](03_gradio_interfaces.ipynb) | `Interface`, streaming callbacks, provider switching, `Blocks` with chained events |
| [04_chat_ui_and_context](04_chat_ui_and_context.ipynb) | `ChatInterface` history handling, system prompt as product spec, conditional context injection |
| [05_tool_calling](05_tool_calling.ipynb) | Tool protocol by hand, parallel and sequential calls, schema generation, streaming with tools |
| [06_multimodal_output](06_multimodal_output.ipynb) | Image generation and text-to-speech, wiring media into a UI |

## Applications

| App | What it does | Run |
|---|---|---|
| [travel_desk](projects/travel_desk/) | Booking assistant for a fictional Lagos-based airline: SQLite-backed fares and bookings, five tools (search, quote, book, look up, cancel), live tool-call log, optional voice replies and destination art | `uv run week02_apis_ui_and_tools/projects/travel_desk/app.py` |
| [tutor_ui.py](projects/tutor_ui.py) | Streaming tech tutor with provider and depth controls; live PyPI/npm lookups so version questions use current data | `uv run week02_apis_ui_and_tools/projects/tutor_ui.py` |

## Toolkit additions

- `toolkit.tools.ToolBox` builds tool JSON schemas from type hints and docstrings, runs the call/execute/respond
  loop in blocking and streaming modes, and returns tool errors to the model instead of raising.
- `toolkit.chat_ui` converts between Gradio chat history and Chat Completions messages.
- `toolkit.llm` adds Anthropic, Groq and OpenRouter providers, `completion()` for raw responses, and
  `available_providers()` (providers with keys configured).

## Notes

- Portability vs features: the compatible endpoint covers most needs, but provider-specific capabilities
  (Anthropic cache breakpoints, content blocks) need the native SDK.
- Prompt caching rewards a **static prefix, variable suffix** layout. Put reference material and instructions
  first and the user's question last.
- Reasoning effort is a per-request dial between cost/latency and accuracy. Trick questions that fail
  at `none` often pass at `low`.
- In streamed responses, tool calls arrive as fragments keyed by index. They must be reassembled before execution.
- Treat model-generated tool arguments as untrusted input: validate inside the tool, and require explicit
  confirmation before side effects.
- llama3.2 (3B) handles parallel and sequential tool calls but sometimes doesn't use a tool result
  in its reply. Frontier models are much more consistent here.
