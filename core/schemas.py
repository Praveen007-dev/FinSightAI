"""Pydantic contracts shared by all agents and the UI."""

from datetime import date as Date
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

Sentiment = Literal["Positive", "Negative", "Neutral", "Mixed", "Unclear"]
EvidenceStatus = Literal["verified", "reported", "allegation", "disputed", "unverified"]
Signal = Literal["BUY", "HOLD", "SELL", "WATCH"]


class CompanyInput(BaseModel):
    name: str = Field(min_length=2)
    symbol: str = Field(min_length=1, max_length=20)
    exchange: Literal["NSE", "BSE"] = "NSE"
    research_period_days: int = Field(default=30, ge=1, le=3650)


class SearchResult(BaseModel):
    title: str = ""
    url: HttpUrl
    snippet: str = ""
    source: str = ""
    published_date: Date | None = None


class NewsFinding(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str
    date: Date | None = None
    source: str = ""
    url: HttpUrl
    summary: str
    category: str = "Other"
    sentiment: Sentiment = "Unclear"
    relevance: str
    financial_impact: str


class NewsAgentOutput(BaseModel):
    company: str
    symbol: str
    research_type: Literal["news"] = "news"
    findings: list[NewsFinding] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    mock_mode: bool = False


class HistoricalEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    event: str
    date: Date | None = None
    category: str = "Corporate"
    description: str
    outcome: str = ""
    source: str = ""
    url: HttpUrl
    fact_status: EvidenceStatus


class HistoryAgentOutput(BaseModel):
    company: str
    symbol: str
    research_type: Literal["history"] = "history"
    findings: list[HistoricalEvent] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    mock_mode: bool = False


class BullishFactor(BaseModel):
    factor: str
    evidence: str
    source_urls: list[HttpUrl] = Field(default_factory=list)


class BearishFactor(BaseModel):
    factor: str
    evidence: str
    source_urls: list[HttpUrl] = Field(default_factory=list)


class FinancialMetric(BaseModel):
    label: str
    value: str
    period: str = "Latest"
    change: str | None = None


class FinancialPoint(BaseModel):
    period: str
    value: float


class FinancialSeries(BaseModel):
    metric: str
    unit: str = ""
    points: list[FinancialPoint] = Field(default_factory=list)


class AnalystOutput(BaseModel):
    company: str
    symbol: str
    signal: Signal
    overall_assessment: str
    confidence: str
    bullish_factors: list[BullishFactor] = Field(default_factory=list)
    bearish_factors: list[BearishFactor] = Field(default_factory=list)
    financial_metrics: list[FinancialMetric] = Field(default_factory=list)
    financial_series: list[FinancialSeries] = Field(default_factory=list)
    historical_context: list[str] = Field(default_factory=list)
    key_developments: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    major_risks: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    time_horizon: str = "Short to medium term"
    disclaimer: str = "This is AI-generated research, not personalized investment advice."
    errors: list[str] = Field(default_factory=list)
    mock_mode: bool = False


class AgentStatus(BaseModel):
    name: str
    status: Literal["pending", "searching", "fetching", "completed", "failed", "analyzing"]
    message: str = ""


class ResearchReport(BaseModel):
    company: CompanyInput
    news: NewsAgentOutput
    history: HistoryAgentOutput
    analysis: AnalystOutput | None = None
    statuses: list[AgentStatus] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    duration_seconds: float = 0.0
    incomplete: bool = False
