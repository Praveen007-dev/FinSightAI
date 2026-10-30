"""Independent TinyFish-powered historical context agent."""

from concurrent.futures import ThreadPoolExecutor, as_completed

from core.config import get_settings
from core.schemas import CompanyInput, HistoricalEvent, HistoryAgentOutput
from core.text import clean_label, clean_source_text
from tinyfish.client import TinyFishClient
from tinyfish.fetch import fetch_research_pages
from tinyfish.search import search_company_information

HISTORY_QUERIES = (
    "site:finance.google.com/quote Google Finance historical price performance financial history",
    "official annual reports historical financial results",
)
MAX_SEARCH_RESULTS = 3
AGENT_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "summary": {"type": "string"},
        "periods": {
            "type": "array",
            "maxItems": 8,
            "items": {"type": "string"},
        },
    },
    "required": ["title", "summary", "periods"],
}


def run_history_agent(company: CompanyInput) -> HistoryAgentOutput:
    settings = get_settings()
    if settings.use_mock_mode:
        return HistoryAgentOutput(
            company=company.name,
            symbol=company.symbol,
            mock_mode=True,
            errors=["Mock mode is active: configure the TinyFish API key for live research."],
        )

    all_results = []
    errors: list[str] = []
    tinyfish = TinyFishClient()
    google_finance_url = f"https://www.google.com/finance/quote/{company.symbol}:{company.exchange}?hl=en"
    try:
        agent_result = tinyfish.run_agent(
            url=google_finance_url,
            goal=(
                f"Extract historical financial context for {company.name} ({company.symbol}) "
                "from this Google Finance page. Return a concise summary and up to 8 explicitly "
                "visible historical or financial periods. Do not include navigation labels or chart controls."
            ),
            output_schema=AGENT_OUTPUT_SCHEMA,
        )
        agent_text = " ".join(
            [str(agent_result.get("summary", ""))]
            + [str(period) for period in agent_result.get("periods", [])]
        )
        agent_page = {
            "url": google_finance_url,
            "title": agent_result.get("title", "Google Finance historical market data"),
            "text": agent_text,
        }
    except Exception as exc:
        agent_page = None
        errors.append(f"TinyFish history agent failed: {exc}")
    with ThreadPoolExecutor(max_workers=len(HISTORY_QUERIES), thread_name_prefix="tinyfish-history") as pool:
        jobs = [
            pool.submit(search_company_information, company.name, query, "history", tinyfish)
            for query in HISTORY_QUERIES
        ]
        for job in as_completed(jobs):
            try:
                results, query_errors = job.result()
                all_results.extend(results)
                errors.extend(query_errors)
            except Exception as exc:
                errors.append(f"TinyFish history search failed: {exc}")

    unique = {google_finance_url: None}
    unique.update({str(result.url): result for result in all_results})
    unique = dict(list(unique.items())[:MAX_SEARCH_RESULTS])
    fetch_urls = [url for url in unique if url != google_finance_url]
    pages, failed_urls = fetch_research_pages(
        fetch_urls,
        "historical corporate research",
        client=tinyfish,
    )
    if agent_page:
        pages.insert(0, agent_page)
    errors.extend(f"Could not fetch source: {url}" for url in failed_urls)
    findings: list[HistoricalEvent] = []
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
            HistoricalEvent(
                event=clean_label(
                    result.title if result else None,
                    "Google Finance historical market data",
                ),
                date=result.published_date if result else None,
                description=clean_source_text(text, max_chars=1000),
                outcome="Not established by the fetched source; analyst review required.",
                source=result.source if result else "",
                url=url,
                fact_status="reported",
            )
        )
    return HistoryAgentOutput(
        company=company.name, symbol=company.symbol, findings=findings, errors=errors
    )
