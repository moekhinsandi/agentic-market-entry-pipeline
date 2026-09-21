"""Optional MCP wrapper for public-source web search / document retrieval.

This client never scrapes sites whose terms prohibit it. It only forwards a
query to a configured MCP (or HTTP) search endpoint. If no endpoint is set,
agents still run and must cite government or company URLs from the prompt.
"""
from __future__ import annotations

import requests

from src.config import config

PREFERRED_SOURCE_DOMAINS = (
    "destatis.de",
    "make-it-in-germany.com",
    "bamf.de",
    "gesetze-im-internet.de",
    "ec.europa.eu",
    "eurostat.ec.europa.eu",
    "arbeitsagentur.de",
    "bundesanzeiger.de",
    "gov.uk",
    "sec.gov",
    "ey.com",
    "kfw.de",
)


def search_public_sources(query: str) -> list[dict[str, str]]:
    """Return search hits from the optional MCP server, or an empty list.

    Expected server contract (fail-open): POST {MCP_SERVER_URL}/search
    with JSON ``{"query": str, "preferred_domains": list[str]}`` and a JSON
    list (or ``{"results": [...]}``) of ``{title, url, snippet}`` objects.
    """
    if not config.mcp_server_url:
        return []

    endpoint = config.mcp_server_url.rstrip("/") + "/search"
    try:
        response = requests.post(
            endpoint,
            json={"query": query, "preferred_domains": list(PREFERRED_SOURCE_DOMAINS)},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return []

    hits = data if isinstance(data, list) else data.get("results", [])
    cleaned: list[dict[str, str]] = []
    for hit in hits[:8]:
        if not isinstance(hit, dict):
            continue
        cleaned.append(
            {
                "title": str(hit.get("title", "")),
                "url": str(hit.get("url", "")),
                "snippet": str(hit.get("snippet", "")),
            }
        )
    return cleaned


def format_search_context(hits: list[dict[str, str]]) -> str:
    if not hits:
        return ""
    lines = [
        "Public-source search hits (cite these URLs when they support a claim; "
        "do not treat snippets as numbers unless the URL is the official source):"
    ]
    for hit in hits:
        lines.append(f"- {hit.get('title', '')} | {hit.get('url', '')} | {hit.get('snippet', '')}")
    return "\n".join(lines)
