"""
Generate a company brochure from its website, in two LLM steps:

  1. Link triage   - the model picks which links (about, careers, products...) are worth reading
  2. Brochure      - the landing page + those pages are condensed into a markdown brochure

    uv run week01_foundations/projects/brochure.py "Hugging Face" https://huggingface.co
    uv run week01_foundations/projects/brochure.py "Hugging Face" https://huggingface.co \\
        --tone witty --audience investors -o brochure.md
"""

import argparse
import sys
from urllib.parse import urlparse

from toolkit import chat, fetch_page, stream

TRIAGE_SYSTEM = """You help research a company from its website.
Given a list of links, choose up to {max_links} that would be most useful for writing
a brochure: about/company, products/services, customers/case studies, careers/culture.
Skip legal pages, login/signup, social media and anything off-site.

Reply with JSON only, shaped like:
{{"links": [{{"type": "about page", "url": "https://example.com/about"}}]}}"""

BROCHURE_SYSTEM = """You write concise company brochures in markdown (no code fences).
Audience: {audience}. Tone: {tone}.
Cover what the company does, who it serves, what makes it different, and its culture
and hiring if the material mentions them. Never invent facts that are not in the material."""


def same_site(url: str, root: str) -> bool:
    return urlparse(url).netloc.removeprefix("www.") == urlparse(root).netloc.removeprefix("www.")


def pick_links(root_url: str, links: list[str], max_links: int, provider: str | None) -> list[dict]:
    candidates = [link for link in links if same_site(link, root_url)]
    if not candidates:
        return []
    result = chat(
        [
            {"role": "system", "content": TRIAGE_SYSTEM.format(max_links=max_links)},
            {"role": "user", "content": f"Site: {root_url}\nLinks:\n" + "\n".join(candidates)},
        ],
        provider=provider,
        as_json=True,
    )
    return result.get("links", [])[:max_links]


def gather_material(root_url: str, max_links: int, provider: str | None) -> str:
    landing = fetch_page(root_url)
    sections = [f"## Landing page\n{landing.as_prompt(2_500)}"]
    for link in pick_links(landing.url, landing.links, max_links, provider):
        print(f"  reading {link['type']}: {link['url']}", file=sys.stderr)
        try:
            sections.append(f"## {link['type']}\n{fetch_page(link['url']).as_prompt(1_500)}")
        except Exception as exc:  # one broken page shouldn't sink the brochure
            print(f"  skipped ({exc})", file=sys.stderr)
    return "\n\n".join(sections)


def brochure(
    company: str,
    url: str,
    tone="professional",
    audience="prospective customers",
    max_links=4,
    provider=None,
):
    material = gather_material(url, max_links, provider)
    messages = [
        {"role": "system", "content": BROCHURE_SYSTEM.format(tone=tone, audience=audience)},
        {"role": "user", "content": f"Company: {company}\n\n{material}"},
    ]
    return stream(messages, provider=provider)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a company brochure from its website")
    parser.add_argument("company")
    parser.add_argument("url")
    parser.add_argument("--tone", default="professional", help="e.g. professional, witty, bold")
    parser.add_argument("--audience", default="prospective customers")
    parser.add_argument("--max-links", type=int, default=4)
    parser.add_argument("-p", "--provider", help="openai | gemini | ollama")
    parser.add_argument("-o", "--out", help="also save the brochure to this file")
    args = parser.parse_args()

    print(f"Researching {args.url} ...", file=sys.stderr)
    text = ""
    for chunk in brochure(
        args.company, args.url, args.tone, args.audience, args.max_links, args.provider
    ):
        print(chunk, end="", flush=True)
        text += chunk
    print()
    if args.out:
        with open(args.out, "w") as f:
            f.write(text)
        print(f"Saved to {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
