from datetime import date

import pytest
from pydantic import ValidationError

from core.schemas import CompanyInput, HistoricalEvent, NewsFinding


def test_company_input_defaults_to_nse() -> None:
    assert CompanyInput(name="Infosys", symbol="INFY").exchange == "NSE"


def test_news_finding_requires_http_url() -> None:
    with pytest.raises(ValidationError):
        NewsFinding(
            title="x",
            url="not-a-url",
            summary="x",
            relevance="x",
            financial_impact="x",
        )


def test_historical_event_preserves_evidence_status() -> None:
    event = HistoricalEvent(
        event="Acquisition",
        date=date(2022, 1, 1),
        description="Reported event",
        url="https://example.com/event",
        fact_status="reported",
    )
    assert event.fact_status == "reported"

