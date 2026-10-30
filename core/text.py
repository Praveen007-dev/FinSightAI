"""Small text-normalization helpers for noisy web research responses."""

import re
from collections.abc import Iterable

_NOISE_LINE = re.compile(
    r"^(?:open menu|sign in|search|home|more|all symbols|moving average|"
    r"moving average convergence divergence|moving average envelope|"
    r"symbol\s*\|\s*price|generating top insights|news stories from web sources)",
    re.IGNORECASE,
)


def clean_source_text(value: object, max_chars: int = 900) -> str:
    """Keep readable source facts while removing common page-navigation noise."""
    text = str(value or "").replace("\r", "\n")
    text = text.replace("·", " ").replace("—", "-").replace("–", "-")
    text = re.sub(
        r"\b(?:Dive Deeper|Line Area Candle Bar|All symbols|Moving average"
        r"(?: convergence divergence| envelope)?|Generating top insights)\b",
        " ",
        text,
        flags=re.IGNORECASE,
    )
    text = re.split(r"\b(?:News stories|From web sources|Profile)\b", text, maxsplit=1, flags=re.IGNORECASE)[0]
    text = re.sub(r"\b(?:Open|Prev Close)\s+₹?[\d,]+(?:\.\d+)?", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"`{1,3}", "", text)
    text = re.sub(r"[*_#]+", "", text)
    text = re.sub(r"[|]+", " ", text)
    text = re.sub(r"\s+\+\s+", " ", text)
    text = re.sub(r"(?m)^\s*[-•]+\s*", "", text)
    lines = re.split(r"\n|(?=All symbols\b)", text)
    lines = [
        re.sub(r"\s+", " ", line).strip(" -|")
        for line in lines
        if line.strip() and not _NOISE_LINE.match(line.strip())
    ]
    text = " ".join(lines)
    kept: list[str] = []
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        sentence = sentence.strip(" -|")
        if sentence and sentence not in kept:
            kept.append(sentence)
    return " ".join(kept)[:max_chars].strip()


def clean_label(value: object, fallback: str) -> str:
    """Return a short, readable title instead of a scraped navigation heading."""
    label = clean_source_text(value, max_chars=140)
    return label or fallback
