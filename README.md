# ai_engineering

Working notes and code from building LLM-powered applications: provider integration,
prompting, multi-step pipelines, RAG, fine-tuning and agents.

| Module | Topic |
|---|---|
| [week01_foundations](week01_foundations/) | Chat Completions, provider abstraction, tokens/context, chained calls with structured output |
| [week02_apis_ui_and_tools](week02_apis_ui_and_tools/) | Provider SDKs and routers, prompt caching, Gradio UIs, function calling, multimodal output |

## Layout

```
toolkit/            shared code reused across modules
  llm.py            provider-agnostic client (OpenAI, Anthropic, Gemini, Groq, OpenRouter, Ollama)
  tools.py          function calling: schemas from type hints, blocking + streaming tool loops
  web.py            single-request page fetch -> title, clean text, absolute links
  chat_ui.py        Gradio chat history <-> Chat Completions messages
  notebook.py       markdown + streaming display for Jupyter
weekNN_<topic>/
  NN_*.ipynb        exploration notebooks
  projects/         standalone CLIs and apps
  README.md         module summary, contents and notes
```

## Setup

Requires [uv](https://docs.astral.sh/uv/); [Ollama](https://ollama.com) for local models.

```bash
uv sync
cp .env.example .env
ollama pull llama3.2
```

`LLM_PROVIDER` sets the default provider (`ollama` | `openai` | `gemini`); every function and CLI
also accepts one explicitly.

```bash
uv run week01_foundations/projects/tech_tutor.py "How does asyncio.gather handle exceptions?"
```

Topics follow Ed Donner's [LLM Engineering](https://github.com/ed-donner/llm_engineering) curriculum.
