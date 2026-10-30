"""TinyFish-powered recent developments agent."""

from concurrent.futures import ThreadPoolExecutor, as_completed

from core.config import get_settings
from core.schemas import CompanyInput, NewsAgentOutput, NewsFinding
from core.text import clean_label, clean_source_text
from tinyfish.client import TinyFishClient
from tinyfish.fetch import fetch_research_pages
from tinyfish.search import search_company_information

NEWS_QUERIES = (
    "site:finance.google.com/quote Google Finance latest price market data earnings revenue EPS",
    "official quarterly results corporate announcements",
)
MAX_SEARCH_RESULTS = 3
AGENT_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "summary": {"type": "string"},
        "price": {"type": "string", "nullable": True},
        "change": {"type": "string", "nullable": True},
        "market_cap": {"type": "string", "nullable": True},
        "eps": {"type": "string", "nullable": True},
        "pe_ratio": {"type": "string", "nullable": True},
    },
    "required": ["title", "summary"],
}


def _google_finance_url(company: CompanyInput) -> str:
    return f"https://www.google.com/finance/quote/{company.symbol}:{company.exchange}?hl=en"


def run_news_agent(company: CompanyInput) -> NewsAgentOutput:
    settings = get_settings()
    if settings.use_mock_mode:
        return NewsAgentOutput(
            company=company.name,
            symbol=company.symbol,
            mock_mode=True,
            errors=["Mock mode is active: configure the TinyFish API key for live research."],
        )

    all_results = []
    errors: list[str] = []
    tinyfish = TinyFishClient()
    google_url = _google_finance_url(company)
    try:
        agent_result = tinyfish.run_agent(
            url=google_url,
            goal=(
                f"Extract current financial information for {company.name} ({company.symbol}) "
                "from this Google Finance page. Return only the page title, a concise summary, "
                "current price, percentage change, market cap, EPS, and P/E ratio. "
                "Do not include navigation labels or chart controls."
            ),
            output_schema=AGENT_OUTPUT_SCHEMA,
        )
        agent_text = " ".join(
            f"{key.replace('_', ' ').title()}: {value}"
            for key, value in agent_result.items()
            if value not in (None, "")
        )
        agent_page = {
            "url": google_url,
            "title": agent_result.get("title", "Google Finance market data"),
            "text": agent_text,
        }
    except Exception as exc:
        agent_page = None
        errors.append(f"TinyFish news agent failed: {exc}")
    with ThreadPoolExecutor(max_workers=len(NEWS_QUERIES), thread_name_prefix="tinyfish-news") as pool:
        jobs = [
            pool.submit(
                search_company_information,
                company.name,
                query,
                "news",
                tinyfish,
                company.research_period_days,
            )
            for query in NEWS_QUERIES
        ]
        for job in as_completed(jobs):
            try:
                results, query_errors = job.result()
                all_results.extend(results)
                errors.extend(query_errors)
            except Exception as exc:
                errors.append(f"TinyFish news search failed: {exc}")

    unique = {google_url: None}
    unique.update({str(result.url): result for result in all_results})
    unique = dict(list(unique.items())[:MAX_SEARCH_RESULTS])
    fetch_urls = [url for url in unique if url != google_url]
    pages, failed_urls = fetch_research_pages(fetch_urls, "recent company news", client=tinyfish)
    if agent_page:
        pages.insert(0, agent_page)
    errors.extend(f"Could not fetch source: {url}" for url in failed_urls)
    findings: list[NewsFinding] = []
    for page in pages:
        url = page.get("url") or page.get("final_url") or page.get("original_url")
        if not url:
            continue
        result = unique.get(url)
        text = str(page.get("text") or page.get("content") or page.get("markdown") or "").strip()
        if not text:
            errors.append(f"Fetched page had no usable content: {url}")
            continue
        findings.append(
            NewsFinding(
                title=clean_label(
                    result.title if result else None,
                    "Google Finance market data",
                ),
                date=result.published_date if result else None,
                source=result.source if result else "",
                url=url,
                summary=clean_source_text(text),
                category="Other",
                sentiment="Unclear",
                relevance="Requires analyst interpretation from the supplied source evidence.",
                financial_impact="Not independently quantified; see source evidence.",
            )
        )
    return NewsAgentOutput(
        company=company.name, symbol=company.symbol, findings=findings, errors=errors
    )
