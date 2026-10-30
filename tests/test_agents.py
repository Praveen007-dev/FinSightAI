from core.config import get_settings
from core.schemas import CompanyInput
from agents.analyst_agent import run_analyst_agent
from agents.history_agent import run_history_agent
from agents.news_agent import run_news_agent


def test_agents_have_structured_mock_outputs(monkeypatch) -> None:
    monkeypatch.setenv("MOCK_MODE", "true")
    get_settings.cache_clear()
    company = CompanyInput(name="Example Ltd", symbol="EXAMPLE")
    assert run_news_agent(company).research_type == "news"
    assert run_history_agent(company).research_type == "history"
    assert run_analyst_agent(company, run_news_agent(company), run_history_agent(company)).signal == "WATCH"
    get_settings.cache_clear()

