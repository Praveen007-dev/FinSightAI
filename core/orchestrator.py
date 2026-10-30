"""Concurrent execution pipeline for the three independent agents."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from time import perf_counter
from typing import Callable

from agents.analyst_agent import run_analyst_agent
from agents.history_agent import run_history_agent
from agents.news_agent import run_news_agent
from core.schemas import (
    AgentStatus,
    CompanyInput,
    HistoryAgentOutput,
    NewsAgentOutput,
    ResearchReport,
)


def run_research(company: CompanyInput, progress: Callable[[str, str, str], None] | None = None) -> ResearchReport:
    started = perf_counter()
    statuses = [
        AgentStatus(name="News Agent", status="searching", message="Searching recent developments."),
        AgentStatus(name="History Agent", status="searching", message="Searching historical records."),
        AgentStatus(name="Analyst Agent", status="pending", message="Waiting for research."),
    ]
    if progress:
        progress("News Agent", "searching", statuses[0].message)
        progress("History Agent", "searching", statuses[1].message)

    news = NewsAgentOutput(company=company.name, symbol=company.symbol)
    history = HistoryAgentOutput(company=company.name, symbol=company.symbol)
    errors: list[str] = []
    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="finsight") as pool:
        jobs = {"News Agent": pool.submit(run_news_agent, company), "History Agent": pool.submit(run_history_agent, company)}
        for name, future in jobs.items():
            try:
                result = future.result()
                if name == "News Agent":
                    news = result
                else:
                    history = result
                if progress:
                    progress(name, "completed", f"{len(result.findings)} findings collected.")
            except Exception as exc:
                errors.append(f"{name} failed: {exc}")
                if progress:
                    progress(name, "failed", str(exc))

    if progress:
        progress("Analyst Agent", "analyzing", "Synthesizing source-linked evidence.")
    try:
        analysis = run_analyst_agent(company, news, history)
        if progress:
            progress(
                "Analyst Agent",
                "failed" if analysis.errors else "completed",
                analysis.errors[0] if analysis.errors else "Analysis completed.",
            )
    except Exception as exc:
        errors.append(f"Analyst Agent failed: {exc}")
        analysis = None
        if progress:
            progress("Analyst Agent", "failed", str(exc))
    errors.extend(news.errors)
    errors.extend(history.errors)
    if analysis:
        errors.extend(analysis.errors)
    return ResearchReport(
        company=company,
        news=news,
        history=history,
        analysis=analysis,
        statuses=statuses,
        errors=list(dict.fromkeys(errors)),
        duration_seconds=round(perf_counter() - started, 2),
        incomplete=bool(news.errors or history.errors or not analysis or analysis.errors),
    )
