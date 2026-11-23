"""
Summarize any (server-rendered) website from the command line.

    uv run week01_foundations/projects/site_summarizer.py https://example.com
    uv run week01_foundations/projects/site_summarizer.py https://example.com --style tldr -p openai
"""

import argparse

from toolkit import fetch_page, stream

STYLES = {
    "neutral": "Write a clear, factual summary in a few short paragraphs.",
    "tldr": "Give a one-line TL;DR followed by at most five bullet points.",
    "snarky": "Write a short, witty, slightly sarcastic summary - but keep the facts right.",
}

SYSTEM = """You summarize website content for a busy reader.
Ignore navigation, cookie banners and footer boilerplate.
If the page contains news or announcements, call them out.
{style}
Respond in plain markdown (no code fences)."""


def summarize(url: str, style: str = "neutral", provider: str | None = None):
    page = fetch_page(url)
    messages = [
        {"role": "system", "content": SYSTEM.format(style=STYLES[style])},
        {"role": "user", "content": f"Website: {page.url}\n\n{page.as_prompt(4_000)}"},
    ]
    return stream(messages, provider=provider)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("url")
    parser.add_argument("--style", choices=STYLES, default="neutral")
    parser.add_argument("-p", "--provider", help="openai | gemini | ollama")
    args = parser.parse_args()

    for chunk in summarize(args.url, args.style, args.provider):
        print(chunk, end="", flush=True)
    print()


if __name__ == "__main__":
    main()
