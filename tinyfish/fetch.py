"""Batched TinyFish Fetch API access."""

from urllib.parse import urlparse

from tinyfish.client import TinyFishClient


def fetch_research_pages(
    urls: list[str],
    purpose: str,
    client: TinyFishClient | None = None,
) -> tuple[list[dict], list[str]]:
    """Fetch up to ten URLs per request and return successes plus failed URLs."""
    unique_urls = list(
        dict.fromkeys(
            url for url in urls
            if isinstance(url, str) and urlparse(url).scheme in {"http", "https"}
        )
    )
    pages: list[dict] = []
    failures: list[str] = []
    api = client or TinyFishClient()
    for start in range(0, len(unique_urls), 10):
        batch = unique_urls[start:start + 10]
        try:
            payload = api.fetch(batch, purpose=purpose, ttl=0)
            items = payload if isinstance(payload, list) else (
                payload.get("results", payload.get("data", []))
                if isinstance(payload, dict) else []
            )
            if not isinstance(items, list):
                items = []
            returned = set()
            for item in items:
                if isinstance(item, dict):
                    page_url = item.get("url") or item.get("final_url") or item.get("original_url")
                    if page_url:
                        returned.add(page_url)
                    pages.append(item)
            failures.extend(url for url in batch if url not in returned)
        except Exception as exc:
            failures.append(f"{batch[0]} (batch failed: {exc})")
            failures.extend(batch[1:])
    return pages, failures
