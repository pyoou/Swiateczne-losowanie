"""Przechowywanie stanu losowania.

Dwa warianty o tym samym interfejsie:
  * JsonStore     – plik JSON na dysku (lokalnie, PythonAnywhere),
  * PostgresStore – baza Postgres (Render i inne hostingi z „ulotnym” dyskiem).

Wybór jest automatyczny: jeśli ustawiono DATABASE_URL, używamy Postgresa.
Oba warianty blokują stan na czas losowania – dwie osoby klikające „Losuj”
w tej samej sekundzie nie wylosują tej samej osoby.
"""
from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from filelock import FileLock

from config import DATABASE_URL, STATE_FILE


class StateMissing(Exception):
    """Losowanie nie zostało jeszcze skonfigurowane."""


class JsonStore:
    def __init__(self, path: Path | str = STATE_FILE):
        self.path = Path(path)
        self._lock = FileLock(str(self.path) + ".lock", timeout=10)

    def exists(self) -> bool:
        return self.path.exists()

    def load(self) -> dict:
        try:
            with self.path.open(encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            raise StateMissing(self.path) from None

    def save(self, state: dict) -> None:
        with self._lock:
            self._write(state)

    def _write(self, state: dict) -> None:
        # Zapis atomowy: plik tymczasowy + os.replace
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)
        except BaseException:
            os.unlink(tmp)
            raise

    @contextmanager
    def transaction(self) -> Iterator[dict]:
        """Wczytaj → zmodyfikuj → zapisz, pod blokadą. Wyjątek = brak zapisu."""
        with self._lock:
            state = self.load()
            yield state
            self._write(state)


class PostgresStore:
    TABLE = "losowanie_stan"

    def __init__(self, url: str):
        import psycopg  # tylko na serwerze – lokalnie niepotrzebny
        from psycopg.types.json import Jsonb

        self._psycopg = psycopg
        self._jsonb = Jsonb
        self.url = url
        with self._connect() as conn:
            conn.execute(f"CREATE TABLE IF NOT EXISTS {self.TABLE} (id INT PRIMARY KEY, data JSONB NOT NULL)")

    def _connect(self):
        # Połączenie jako context manager: commit przy sukcesie, rollback przy wyjątku.
        return self._psycopg.connect(self.url, connect_timeout=10)

    def exists(self) -> bool:
        with self._connect() as conn:
            return conn.execute(f"SELECT 1 FROM {self.TABLE} WHERE id = 1").fetchone() is not None

    def load(self) -> dict:
        with self._connect() as conn:
            row = conn.execute(f"SELECT data FROM {self.TABLE} WHERE id = 1").fetchone()
        if row is None:
            raise StateMissing("baza danych")
        return row[0]

    def save(self, state: dict) -> None:
        with self._connect() as conn:
            conn.execute(
                f"INSERT INTO {self.TABLE} (id, data) VALUES (1, %s) "
                "ON CONFLICT (id) DO UPDATE SET data = EXCLUDED.data",
                (self._jsonb(state),),
            )

    @contextmanager
    def transaction(self) -> Iterator[dict]:
        with self._connect() as conn:
            # FOR UPDATE blokuje wiersz do końca transakcji.
            row = conn.execute(f"SELECT data FROM {self.TABLE} WHERE id = 1 FOR UPDATE").fetchone()
            if row is None:
                raise StateMissing("baza danych")
            state = row[0]
            yield state
            conn.execute(f"UPDATE {self.TABLE} SET data = %s WHERE id = 1", (self._jsonb(state),))


Store = JsonStore | PostgresStore


def make_store() -> Store:
    return PostgresStore(DATABASE_URL) if DATABASE_URL else JsonStore()
