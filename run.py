"""Uruchamia serwer produkcyjny (waitress – działa też na Windowsie)."""
import os
import sys

from waitress import serve

from app import app

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # emoji w konsoli Windows
    port = int(os.environ.get("PORT", 8000))
    print(f"🎄 Świąteczne Losowanie działa na http://localhost:{port}")
    print("   Aby udostępnić rodzinie, w drugim terminalu uruchom:")
    print(f"   cloudflared tunnel --url http://localhost:{port}\n")
    serve(app, host="0.0.0.0", port=port, threads=8)
