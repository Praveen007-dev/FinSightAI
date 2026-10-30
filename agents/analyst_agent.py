"""TinyFish-powered evidence synthesis agent."""

import json
import re
from typing import Any

from core.config import get_settings
from core.schemas import AnalystOutput, CompanyInput, HistoryAgentOutput, NewsAgentOutput
from tinyfish.client import TinyFishClient


ANALYST_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "signal": {"type": "string", "enum": ["BUY", "HOLD", "SELL", "WATCH"]},
        "overall_assessment": {"type": "string"},
        "confidence": {"type": "string"},
        "bullish_factors": {
            "type": "array",
            "maxItems": 5,
            "items": {
                "type": "object",
                "properties": {
                    "factor": {"type": "string"},
                    "evidence": {"type": "string"},
                    "source_urls": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
                },
                "required": ["factor", "evidence", "source_urls"],
            },
        },
        "bearish_factors": {
            "type": "array",
            "maxItems": 5,
            "items": {
                "type": "object",
                "properties": {
                    "factor": {"type": "string"},
                    "evidence": {"type": "string"},
                    "source_urls": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
                },
                "required": ["factor", "evidence", "source_urls"],
            },
        },
        "financial_metrics": {
            "type": "array",
            "maxItems": 4,
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "value": {"type": "string"},
                    "period": {"type": "string"},
                    "change": {"type": "string", "nullable": True},
                },
                "required": ["label", "value", "period", "change"],
            },
        },
        "historical_context": {"type": "array", "maxItems": 5, "items": {"type": "string"}},
        "key_developments": {"type": "array", "maxItems": 5, "items": {"type": "string"}},
        "major_risks": {"type": "array", "maxItems": 5, "items": {"type": "string"}},
        "opportunities": {"type": "array", "maxItems": 5, "items": {"type": "string"}},
        "uncertainties": {"type": "array", "maxItems": 5, "items": {"type": "string"}},
        "time_horizon": {"type": "string"},
    },
    "required": [
        "signal", "overall_assessment", "confidence", "bullish_factors",
        "bearish_factors", "financial_metrics", "historical_context",
        "key_developments", "major_risks", "opportunities", "uncertainties",
        "time_horizon",
    ],
}


def _clean_text(value: str) -> str:
    cleaned = re.sub(r"[*_`#]+", "", value)
    cleaned = re.sub(r"^\s*[-•]+\s*", "", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def _mock_analysis(company: CompanyInput, news: NewsAgentOutput, history: HistoryAgentOutput) -> AnalystOutput:
    return AnalystOutput(
        company=company.name,
        symbol=company.symbol,
        signal="WATCH",
        overall_assessment=(
            "No live evidence was analyzed. Configure the TinyFish API key and rerun the "
            "research to produce an evidence-based assessment."
        ),
        confidence="Low",
        uncertainties=["The TinyFish API key is not configured."],
        errors=["Mock mode is active; this is not investment research."],
        mock_mode=True,
    )


def _fallback_analysis(
    company: CompanyInput,
    news: NewsAgentOutput,
    history: HistoryAgentOutput,
    error: Exception,
) -> AnalystOutput:
    """Keep the report useful when the final TinyFish synthesis times out."""
    news_items = news.findings[:5]
    history_items = history.findings[:5]
    positives = [
        {
            "factor": item.title,
            "evidence": _clean_text(item.summary)[:240],
            "source_urls": [str(item.url)],
        }
        for item in news_items
        if item.summary
    ]
    historical = [_clean_text(item.description)[:240] for item in history_items if item.description]
    developments = [_clean_text(item.summary)[:240] for item in news_items if item.summary]
    risks = [
        {
            "factor": "Downside evidence requires confirmation",
            "evidence": "The fetched sources did not establish a quantified downside factor.",
            "source_urls": [str(item.url) for item in history_items[:1]],
        }
    ]
    watch_next = [
        "Review the next quarterly results and compare revenue, EPS, and margin trends.",
        "Monitor whether the current market price move is supported by reported fundamentals.",
    ]
    return AnalystOutput(
        company=company.name,
        symbol=company.symbol,
        signal="WATCH",
        overall_assessment="TinyFish collected source evidence, but its final synthesis timed out. The evidence is shown directly for review.",
        confidence="Low",
        bullish_factors=positives,
        bearish_factors=risks,
        historical_context=historical,
        key_developments=developments,
        major_risks=["No quantified downside risk was established by the fetched sources."],
        opportunities=["Use the next reported quarterly figures to confirm whether current momentum is fundamental."],
        uncertainties=["Final TinyFish synthesis timed out; review the linked source evidence."],
        time_horizon="Next quarterly reporting cycle",
        errors=[f"TinyFish analysis failed: {error}"],
    )


def _input_payload(company: CompanyInput, news: NewsAgentOutput, history: HistoryAgentOutput) -> dict[str, Any]:
    news_payload = news.model_dump(mode="json")
    history_payload = history.model_dump(mode="json")
    for finding in news_payload["findings"]:
        finding["summary"] = finding["summary"][:900]
    for event in history_payload["findings"]:
        event["description"] = event["description"][:1100]
    return {
        "company": company.model_dump(mode="json"),
        "news": news_payload,
        "history": history_payload,
        "required_fields": list(AnalystOutput.model_fields),
    }


def _normalize_response(parsed: dict[str, Any]) -> dict[str, Any]:
    """Keep useful model output when providers vary slightly from the schema."""
    normalized = dict(parsed)
    if "confidence" in normalized and not isinstance(normalized["confidence"], str):
        normalized["confidence"] = str(normalized["confidence"])
    for key in ("historical_context", "key_developments", "contradictions", "major_risks", "opportunities", "uncertainties"):
        value = normalized.get(key)
        if isinstance(value, str):
            normalized[key] = [value]
    for key in ("bullish_factors", "bearish_factors"):
        factors = normalized.get(key)
        if isinstance(factors, list):
            normalized[key] = [
                {"factor": item, "evidence": item, "source_urls": []}
                if isinstance(item, str) else item
                for item in factors
            ]
    metrics = normalized.get("financial_metrics")
    if isinstance(metrics, list):
        normalized["financial_metrics"] = [
            {"label": item.get("label", "Metric"), "value": str(item.get("value", "")), "period": str(item.get("period", "Latest")), "change": item.get("change")}
            if isinstance(item, dict) else {"label": "Metric", "value": str(item), "period": "Latest"}
            for item in metrics[:4]
        ]
    series = normalized.get("financial_series")
    if isinstance(series, list):
        normalized["financial_series"] = [
            {
                "metric": str(item.get("metric", "Metric")),
                "unit": str(item.get("unit", "")),
                "points": [
                    {"period": str(point.get("period", "")), "value": float(point["value"])}
                    for point in item.get("points", [])
                    if isinstance(point, dict) and point.get("period") and isinstance(point.get("value"), (int, float))
                ][:8],
            }
            for item in series[:4]
            if isinstance(item, dict)
        ]
    for key in ("key_developments", "major_risks", "uncertainties"):
        items = normalized.get(key)
        if isinstance(items, list):
            normalized[key] = [_clean_text(str(item)) for item in items[:5]]
    for key in ("overall_assessment", "confidence", "time_horizon"):
        if isinstance(normalized.get(key), str):
            normalized[key] = _clean_text(normalized[key])
    for key in ("bullish_factors", "bearish_factors"):
        factors = normalized.get(key)
        if isinstance(factors, list):
            normalized[key] = [
                {
                    **item,
                    "factor": _clean_text(str(item.get("factor", ""))),
                    "evidence": _clean_text(str(item.get("evidence", ""))),
                }
                for item in factors[:5]
                if isinstance(item, dict)
            ]
    return normalized


def run_analyst_agent(
    company: CompanyInput,
    news: NewsAgentOutput,
    history: HistoryAgentOutput,
) -> AnalystOutput:
    settings = get_settings()
    if settings.use_mock_mode:
        return _mock_analysis(company, news, history)

    try:
        client = TinyFishClient()
        evidence = json.dumps(_input_payload(company, news, history), default=str)
        result = client.run_agent(
            url=f"https://www.google.com/finance/quote/{company.symbol}:{company.exchange}?hl=en",
            goal=(
                f"You are the final financial analyst for {company.name} ({company.symbol}). "
                "Use the supplied TinyFish research evidence and the Google Finance page. "
                "Return a complete structured financial briefing. Populate every required list "
                "when supported by evidence: bullish_factors for positives, bearish_factors for "
                "risks, historical_context for past results, key_developments for recent facts, "
                "major_risks for downside concerns, opportunities for upside drivers, and "
                "uncertainties only for genuinely missing or conflicting data. Keep each item "
                "concise, financial, company-specific, and free of Markdown symbols. Never invent "
                f"facts or numbers. Evidence JSON: {evidence}"
            ),
            output_schema=ANALYST_OUTPUT_SCHEMA,
        )
        return AnalystOutput.model_validate(
            {**_normalize_response(result), "company": company.name, "symbol": company.symbol}
        )
    except Exception as exc:
        return _fallback_analysis(company, news, history, exc)
