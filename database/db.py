"""Minimal SQLite storage for completed reports."""

import json
import sqlite3
from pathlib import Path

from core.config import get_settings
from core.schemas import ResearchReport


def _path() -> str:
    url = get_settings().database_url
    return url.removeprefix("sqlite:///") if url.startswith("sqlite:///") else "finsight.db"


def initialize() -> None:
    Path(_path()).parent.mkdir(parents=True, exist_ok=True) if Path(_path()).parent != Path(".") else None
    with sqlite3.connect(_path()) as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS reports (id INTEGER PRIMARY KEY, symbol TEXT, company TEXT, payload TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)"
        )


def save_report(report: ResearchReport) -> None:
    initialize()
    with sqlite3.connect(_path()) as connection:
        connection.execute(
            "INSERT INTO reports(symbol, company, payload) VALUES (?, ?, ?)",
            (report.company.symbol, report.company.name, json.dumps(report.model_dump(mode="json"))),
        )

