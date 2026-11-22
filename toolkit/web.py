"""Fetch a web page once and extract both its readable text and its links."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urldefrag, urljoin

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
    )
}
NOISE_TAGS = ["script", "style", "noscript", "svg", "img", "input", "iframe"]
SKIP_SCHEMES = ("mailto:", "tel:", "javascript:")


@dataclass
class Page:
    url: str
    title: str
    text: str
    links: list[str]

    def as_prompt(self, max_chars: int = 2_000) -> str:
        """Title + body text, truncated so prompts stay small (and cheap)."""
        return f"{self.title}\n\n{self.text}"[:max_chars]


def fetch_page(url: str, timeout: float = 15) -> Page:
    """
    Download a page with a single request. Links are returned as absolute URLs,
    de-duplicated, with fragments and mailto/tel links removed.

    Note: JavaScript-rendered sites (many React apps) return little or no text here.
    """
    response = requests.get(url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")

    title = soup.title.get_text(strip=True) if soup.title else "Untitled"

    links: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(SKIP_SCHEMES) or href.startswith("#"):
            continue
        absolute = urldefrag(urljoin(response.url, href)).url
        if absolute not in links:
            links.append(absolute)

    body = soup.body or soup
    for tag in body(NOISE_TAGS):
        tag.decompose()
    text = body.get_text(separator="\n", strip=True)

    return Page(url=response.url, title=title, text=text, links=links)
