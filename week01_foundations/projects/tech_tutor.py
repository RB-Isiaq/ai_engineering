"""
A terminal tech tutor: ask a programming question, get a streamed explanation.

    uv run week01_foundations/projects/tech_tutor.py "What does yield from do in Python?"
    uv run week01_foundations/projects/tech_tutor.py --compare openai ollama "Explain JS closures"
    uv run week01_foundations/projects/tech_tutor.py          # interactive mode, keeps context
"""

import argparse

from toolkit import PROVIDERS, stream

SYSTEM = """You are a patient senior engineer tutoring a developer.
Explain the concept or code they ask about: what it does, why it works that way,
and a tiny example. Mention a common pitfall if there is one.
Be concise. Use markdown and fenced code blocks for code."""


def answer(messages: list[dict], provider: str | None) -> str:
    text = ""
    for chunk in stream(messages, provider=provider):
        print(chunk, end="", flush=True)
        text += chunk
    print("\n")
    return text


def one_shot(question: str, providers: list[str | None]) -> None:
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]
    for provider in providers:
        if len(providers) > 1:
            print(f"\n===== {provider} ({PROVIDERS[provider].default_model}) =====\n")
        answer(messages, provider)


def interactive(provider: str | None) -> None:
    """Follow-up questions work because the whole history is resent each turn."""
    messages = [{"role": "system", "content": SYSTEM}]
    print("Ask away (blank line or Ctrl-D to quit).\n")
    while True:
        try:
            question = input("you> ").strip()
        except EOFError:
            break
        if not question:
            break
        messages.append({"role": "user", "content": question})
        messages.append({"role": "assistant", "content": answer(messages, provider)})


def main() -> None:
    parser = argparse.ArgumentParser(description="Stream explanations of technical questions")
    parser.add_argument("question", nargs="?", help="omit for interactive mode")
    parser.add_argument("-p", "--provider", help="openai | gemini | ollama")
    parser.add_argument(
        "--compare", nargs="+", metavar="PROVIDER", help="ask several providers the same question"
    )
    args = parser.parse_args()

    if args.question:
        one_shot(args.question, args.compare or [args.provider])
    else:
        interactive(args.provider)


if __name__ == "__main__":
    main()
