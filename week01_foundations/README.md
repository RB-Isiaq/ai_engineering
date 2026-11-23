# week01_foundations

This module covers the fundamentals that everything later builds on. It looks at what an LLM API call
actually is, why one client works across vendors and local models, how tokens and statelessness constrain
application design, and how to break a task into a pipeline of focused model calls with structured output.
The result is a provider-agnostic toolkit and three CLI tools.

| Notebook | Scope |
|---|---|
| [01_chat_completions](01_chat_completions.ipynb) | Request structure, system vs user prompts, page summarization |
| [02_providers_and_endpoints](02_providers_and_endpoints.ipynb) | Raw HTTP vs SDK, OpenAI-compatible endpoints, local and reasoning models |
| [03_tokens_and_context](03_tokens_and_context.ipynb) | Tokenization efficiency, cost estimation, statelessness and history growth |
| [04_brochure_pipeline](04_brochure_pipeline.ipynb) | Two-stage pipeline: JSON page selection → streamed generation |

## CLI tools

| Tool | Usage |
|---|---|
| `site_summarizer.py` | `uv run week01_foundations/projects/site_summarizer.py <url> [--style neutral\|tldr\|snarky]` |
| `brochure.py` | `uv run week01_foundations/projects/brochure.py "<company>" <url> [--tone] [--audience] [-o out.md]` |
| `tech_tutor.py` | `uv run week01_foundations/projects/tech_tutor.py ["question"] [--compare ollama openai]` (no args = interactive) |

All accept `-p/--provider`.

## Notes

- The OpenAI SDK is a thin HTTP wrapper; since vendors converged on the Chat Completions contract,
  provider choice reduces to `base_url` + key + model, hence `toolkit.llm.PROVIDERS`.
- Tokens drive cost, latency and context limits. Non-English text and code tokenize far less
  efficiently than English prose, so scraped input is always truncated.
- Models are stateless; conversation state is client-managed and grows linearly per turn.
- Splitting work into code steps (fetch, filter) and model steps (select, write) gives smaller prompts
  and more predictable output. JSON mode plus a one-shot schema example makes model output consumable.
- Plain HTTP scraping fails on JS-rendered sites; context quality bounds output quality.
- llama3.2 (3B) is fine for summarization but weaker on schema adherence and grounding than frontier models.
