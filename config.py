"""Wspólne ustawienia aplikacji (nadpisywane zmiennymi środowiskowymi)."""
from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent
STATE_FILE = Path(os.environ.get("LOSOWANIE_STAN", BASE_DIR / "data" / "stan.json"))
TZ = ZoneInfo(os.environ.get("LOSOWANIE_TZ", "Europe/Warsaw"))
# Ustawione → stan trzymany w Postgresie zamiast w pliku.
DATABASE_URL = os.environ.get("DATABASE_URL", "")
# Hasło do strony /setup. Puste → konfiguracja przez stronę wyłączona.
SETUP_KEY = os.environ.get("SETUP_KEY", "")


def now() -> datetime:
    return datetime.now(TZ)


def is_open(state: dict) -> bool:
    return now() <= datetime.fromisoformat(state["deadline"])


def days_to_christmas_eve(today: date | None = None) -> int:
    today = today or now().date()
    eve = date(today.year, 12, 24)
    if today > eve:
        eve = date(today.year + 1, 12, 24)
    return (eve - today).days
