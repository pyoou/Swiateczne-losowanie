"""Przygotowuje losowanie z konsoli: czyta uczestników, generuje osobiste linki.

Na hostingu bez konsoli (np. Render) użyj zamiast tego strony /setup.

Użycie:
    python setup_losowania.py                       # aktywne dziś do 23:59
    python setup_losowania.py --do 21:00            # dziś do 21:00
    python setup_losowania.py --do "2026-12-06 20:00"
    python setup_losowania.py --nadpisz             # zacznij od nowa (nowe linki!)
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, time
from pathlib import Path

from config import BASE_DIR, TZ, now
from draw import new_state, parse_names
from storage import make_store


def parse_deadline(value: str | None) -> datetime:
    if value is None:
        return datetime.combine(now().date(), time(23, 59, 59), TZ)
    try:
        return datetime.combine(now().date(), time.fromisoformat(value), TZ)
    except ValueError:
        return datetime.fromisoformat(value).replace(tzinfo=TZ)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # emoji w konsoli Windows
    parser = argparse.ArgumentParser(description="Przygotuj świąteczne losowanie.")
    parser.add_argument("--plik", default=BASE_DIR / "uczestnicy.txt", type=Path,
                        help="plik z imionami, jedno w linii (domyślnie uczestnicy.txt)")
    parser.add_argument("--do", dest="deadline", help="do kiedy można losować, np. 21:00 lub '2026-12-06 20:00'")
    parser.add_argument("--url", default="http://localhost:8000", help="adres strony do wypisania linków")
    parser.add_argument("--nadpisz", action="store_true", help="usuń istniejące losowanie i zacznij od nowa")
    args = parser.parse_args()

    store = make_store()
    if store.exists() and not args.nadpisz:
        sys.exit("⚠️  Losowanie już istnieje. Użyj --nadpisz, aby zacząć od nowa (stare linki przestaną działać).")

    try:
        names = parse_names(args.plik.read_text(encoding="utf-8"))
    except ValueError as e:
        sys.exit(f"❌ {e}")
    deadline = parse_deadline(args.deadline)
    state = new_state(names, deadline)
    store.save(state)

    url = args.url.rstrip("/")
    print(f"\n🎄 Losowanie gotowe! {len(names)} osób, aktywne do {deadline:%d.%m.%Y %H:%M}\n")
    print(f"🔑 Panel organizatora (NIE wysyłaj nikomu):\n   {url}/admin/{state['admin_token']}\n")
    print("🎁 Osobiste linki (wygodniej skopiujesz je z panelu organizatora):")
    for p in state["participants"]:
        print(f"   {p['name']:<20} {url}/l/{p['token']}")
    print()


if __name__ == "__main__":
    main()
