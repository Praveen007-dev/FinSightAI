from core.config import get_settings
from core.orchestrator import run_research
from core.schemas import CompanyInput


def test_orchestrator_completes_in_mock_mode(monkeypatch) -> None:
    monkeypatch.setenv("MOCK_MODE", "true")
    get_settings.cache_clear()
    report = run_research(CompanyInput(name="Example Ltd", symbol="EXAMPLE"))
    assert report.analysis is not None
    assert report.analysis.signal == "WATCH"
    get_settings.cache_clear()

