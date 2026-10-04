"""Logika losowania – czysta, bez Flaska, łatwa do przetestowania.

Zasady:
  * każda osoba może zostać wylosowana tylko raz (pula się zmniejsza),
  * kto wylosuje samego siebie, dostaje JEDNĄ dodatkową próbę
    (w niej nie da się już trafić na siebie),
  * nie ma zamiany – raz wylosowana osoba zostaje na stałe,
  * algorytm pilnuje, żeby ostatnia osoba nie została sama ze sobą w puli.
"""
from __future__ import annotations

import random
import secrets
from datetime import datetime
from typing import Any

from config import now

Participant = dict[str, Any]


class DrawError(Exception):
    """Losowanie nie może zostać wykonane."""


def parse_names(text: str) -> list[str]:
    """Imiona z tekstu (jedno w linii, # = komentarz). ValueError, jeśli coś nie tak."""
    names = [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]
    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        raise ValueError(f"Powtórzone imiona: {', '.join(duplicates)} – dodaj np. inicjał nazwiska.")
    if len(names) < 2:
        raise ValueError("Do losowania potrzeba co najmniej 2 osób.")
    return names


def new_state(names: list[str], deadline: datetime) -> dict[str, Any]:
    return {
        "admin_token": secrets.token_urlsafe(12),
        "deadline": deadline.isoformat(timespec="seconds"),
        "created_at": now().isoformat(timespec="seconds"),
        "participants": [
            {"name": n, "token": secrets.token_urlsafe(8), "result": None, "self_hit": False, "drawn_at": None}
            for n in names
        ],
    }


def find_by_token(participants: list[Participant], token: str) -> Participant | None:
    return next((p for p in participants if p["token"] == token), None)


def available_pool(participants: list[Participant]) -> list[str]:
    """Osoby, których nikt jeszcze nie wylosował."""
    taken = {p["result"] for p in participants if p["result"]}
    return [p["name"] for p in participants if p["name"] not in taken]


def candidates_for(participants: list[Participant], me: Participant) -> list[str]:
    pool = available_pool(participants)
    others_waiting = [p["name"] for p in participants if not p["result"] and p is not me]

    # Ochrona przed ślepym zaułkiem: jeśli po mnie zostanie już tylko jedna osoba
    # i ona sama wciąż jest w puli, muszę wylosować właśnie ją – inaczej zostałaby
    # na końcu sama ze sobą.
    if len(others_waiting) == 1 and others_waiting[0] in pool:
        return others_waiting

    if me["self_hit"]:
        # Dodatkowa próba po trafieniu na siebie – tym razem bez siebie w puli.
        return [name for name in pool if name != me["name"]]

    # Pierwsza próba: uczciwie, jak z kapelusza – można trafić na siebie.
    return pool


def perform_draw(participants: list[Participant], me: Participant, rng: random.Random) -> dict[str, Any]:
    """Losuje dla `me` i modyfikuje `participants` w miejscu."""
    if me["result"]:
        return {"status": "ok", "result": me["result"], "already": True}

    candidates = candidates_for(participants, me)
    if not candidates:
        raise DrawError("Brak osób do wylosowania – to nie powinno się zdarzyć.")

    pick = rng.choice(candidates)
    if pick == me["name"]:
        me["self_hit"] = True
        return {"status": "self"}

    me["result"] = pick
    me["drawn_at"] = now().isoformat(timespec="seconds")
    return {"status": "ok", "result": pick}


def progress(participants: list[Participant]) -> dict[str, int]:
    done = sum(1 for p in participants if p["result"])
    total = len(participants)
    return {"done": done, "total": total, "percent": round(100 * done / total) if total else 0}
