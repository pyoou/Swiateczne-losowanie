"""Świąteczne Losowanie – aplikacja Flask."""
from __future__ import annotations

import secrets
from datetime import datetime, time

from flask import Flask, abort, jsonify, redirect, render_template, request, url_for
from werkzeug.middleware.proxy_fix import ProxyFix

import config
from config import TZ, days_to_christmas_eve, is_open, now
from draw import DrawError, find_by_token, new_state, parse_names, perform_draw, progress
from storage import StateMissing, Store, make_store

MONTHS = ["stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca", "lipca",
          "sierpnia", "września", "października", "listopada", "grudnia"]


def create_app(store: Store | None = None, setup_key: str | None = None) -> Flask:
    app = Flask(__name__)
    # Za tunelem (cloudflared/ngrok) lub proxy – żeby linki miały poprawny adres i https.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    store = store or make_store()
    setup_key = config.SETUP_KEY if setup_key is None else setup_key
    rng = secrets.SystemRandom()

    @app.template_filter("pl_datetime")
    def pl_datetime(value: str) -> str:
        dt = datetime.fromisoformat(value)
        return f"{dt.day} {MONTHS[dt.month - 1]}, godz. {dt:%H:%M}"

    def load_state() -> dict:
        try:
            return store.load()
        except StateMissing:
            abort(503)

    def require_admin(state: dict, token: str) -> None:
        if not secrets.compare_digest(token, state["admin_token"]):
            abort(404)

    @app.get("/")
    def index():
        state = load_state()
        return render_template(
            "index.html",
            progress=progress(state["participants"]),
            deadline=state["deadline"],
            is_open=is_open(state),
            days_to_eve=days_to_christmas_eve(),
        )

    @app.get("/l/<token>")
    def person(token: str):
        state = load_state()
        participants = state["participants"]
        me = find_by_token(participants, token) or abort(404)
        data = {
            "me": me["name"],
            "result": me["result"],
            "pendingRedraw": me["self_hit"] and not me["result"],
            "closed": not is_open(state),
            "names": [p["name"] for p in participants],
            "drawUrl": url_for("api_draw", token=token),
        }
        return render_template("draw.html", me=me, data=data, deadline=state["deadline"])

    @app.post("/api/draw/<token>")
    def api_draw(token: str):
        try:
            with store.transaction() as state:
                me = find_by_token(state["participants"], token)
                if me is None:
                    return jsonify(error="Nieznany link."), 404
                if not me["result"] and not is_open(state):
                    return jsonify(error="Losowanie zostało już zamknięte. 🔒"), 410
                outcome = perform_draw(state["participants"], me, rng)
        except StateMissing:
            return jsonify(error="Losowanie nie jest jeszcze skonfigurowane."), 503
        except DrawError as e:
            return jsonify(error=str(e)), 409
        return jsonify(outcome)

    @app.get("/admin/<token>")
    def admin(token: str):
        state = load_state()
        require_admin(state, token)
        base = request.host_url.rstrip("/")
        people = [
            {
                "name": p["name"],
                "link": base + url_for("person", token=p["token"]),
                "done": bool(p["result"]),
                "self_hit": p["self_hit"],
                "drawn_at": p["drawn_at"],
            }
            for p in state["participants"]
        ]
        return render_template(
            "admin.html",
            people=people,
            progress=progress(state["participants"]),
            deadline=state["deadline"],
            is_open=is_open(state),
            token=token,
            is_new=bool(request.args.get("nowe")),
            admin_url=base + url_for("admin", token=token),
        )

    @app.post("/admin/<token>/reset")
    def admin_reset(token: str):
        with store.transaction() as state:
            require_admin(state, token)
            for p in state["participants"]:
                p.update(result=None, self_hit=False, drawn_at=None)
        return redirect(url_for("admin", token=token))

    @app.get("/healthz")
    def healthz():
        return "ok"

    # ---------- Konfiguracja przez stronę (dla hostingu bez konsoli) ----------

    @app.route("/setup", methods=["GET", "POST"])
    def setup():
        if not setup_key:
            abort(404)
        exists = store.exists()
        form = {
            "names": "",
            "deadline": datetime.combine(now().date(), time(23, 59)).strftime("%Y-%m-%dT%H:%M"),
        }
        error = None
        if request.method == "POST":
            form = {"names": request.form.get("names", ""), "deadline": request.form.get("deadline", "")}
            try:
                if not secrets.compare_digest(request.form.get("key", ""), setup_key):
                    raise ValueError("Nieprawidłowe hasło organizatora.")
                if exists and not request.form.get("overwrite"):
                    raise ValueError("Losowanie już istnieje – zaznacz „Zacznij od nowa”, żeby je zastąpić.")
                names = parse_names(form["names"])
                try:
                    deadline = datetime.fromisoformat(form["deadline"]).replace(tzinfo=TZ)
                except ValueError:
                    raise ValueError("Podaj poprawny termin zakończenia losowania.") from None
                if deadline <= now():
                    raise ValueError("Termin zakończenia musi być w przyszłości.")
            except ValueError as e:
                error = str(e)
            else:
                state = new_state(names, deadline)
                store.save(state)
                return redirect(url_for("admin", token=state["admin_token"], nowe=1))
        return render_template("setup.html", form=form, error=error, exists=exists), 400 if error else 200

    @app.errorhandler(404)
    def not_found(_):
        return render_template(
            "message.html",
            emoji="🦌",
            title="Renifer zgubił drogę",
            text="Tej strony nie ma. Sprawdź, czy link od organizatora został skopiowany w całości.",
        ), 404

    @app.errorhandler(503)
    def not_configured(_):
        return render_template(
            "message.html",
            emoji="🎅",
            title="Mikołaj jeszcze się szykuje",
            text="Losowanie nie zostało jeszcze przygotowane. Organizator: wejdź na stronę /setup.",
        ), 503

    return app


app = create_app()
