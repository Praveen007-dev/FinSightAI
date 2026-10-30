"""Normalized TinyFish Search API access."""

from datetime import date
from urllib.parse import urlparse

from core.schemas import SearchResult
from tinyfish.client import TinyFishClient


def _items(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("results", "items", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def search_company_information(
    company_name: str,
    query: str,
    research_type: str,
    client: TinyFishClient | None = None,
    days: int | None = None,
) -> tuple[list[SearchResult], list[str]]:
    """Search and normalize results while retaining malformed-result errors."""
    errors: list[str] = []
    try:
        payload = (client or TinyFishClient()).search(
            query=f"{company_name} {query}",
            type="news" if research_type == "news" else "web",
            recency=days,
        )
    except Exception as exc:
        return [], [f"TinyFish search failed: {exc}"]

    results: list[SearchResult] = []
    seen: set[str] = set()
    for item in _items(payload):
        url = item.get("url") or item.get("link")
        if not isinstance(url, str) or url in seen or urlparse(url).scheme not in {"http", "https"}:
            continue
        seen.add(url)
        try:
            published = item.get("published_date") or item.get("date")
            published_date = None
            if isinstance(published, str) and len(published) >= 10:
                try:
                    published_date = date.fromisoformat(published[:10])
                except ValueError:
                    published_date = None
            results.append(
                SearchResult(
                    title=str(item.get("title") or ""),
                    url=url,
                    snippet=str(item.get("snippet") or item.get("description") or ""),
                    source=str(item.get("source") or item.get("publisher") or ""),
                    published_date=published_date,
                )
            )
        except Exception as exc:
            errors.append(f"Skipped malformed search result: {exc}")
    return results, errors
