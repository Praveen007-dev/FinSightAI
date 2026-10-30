from core.text import clean_label, clean_source_text


def test_clean_source_text_removes_navigation_and_markdown_noise() -> None:
    value = "## Financial results | *Revenue* ₹1,000 crore\nAll symbols * Moving average\nRevenue grew 12%."
    assert clean_source_text(value) == "Financial results Revenue ₹1,000 crore Revenue grew 12%."


def test_clean_label_uses_fallback_for_empty_scraped_title() -> None:
    assert clean_label("### ***", "Google Finance market data") == "Google Finance market data"
