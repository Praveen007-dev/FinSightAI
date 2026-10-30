from tinyfish.fetch import fetch_research_pages
from tinyfish.search import search_company_information


class FakeClient:
    def search(self, **kwargs):
        return {"results": [{"title": "A", "url": "https://example.com/a", "snippet": "x"}]}

    def fetch(self, urls, **kwargs):
        return {"results": [{"url": urls[0], "title": "A", "text": "content"}]}


def test_search_normalizes_results() -> None:
    results, errors = search_company_information("Infosys", "news", "news", client=FakeClient())
    assert len(results) == 1
    assert not errors


def test_fetch_deduplicates_and_returns_failures() -> None:
    pages, failures = fetch_research_pages(
        ["https://example.com/a", "https://example.com/a", "https://example.com/b"],
        "test",
        client=FakeClient(),
    )
    assert len(pages) == 1
    assert failures == ["https://example.com/b"]

