import os
import random
import sys
from datetime import timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app  # noqa: E402
from config import now  # noqa: E402
from draw import candidates_for, perform_draw  # noqa: E402
from storage import JsonStore, PostgresStore, StateMissing  # noqa: E402


def make_participants(n):
    return [
        {"name": f"Osoba{i}", "token": f"t{i}", "result": None, "self_hit": False, "drawn_at": None}
        for i in range(n)
    ]


def run_full_draw(participants, rng):
    """Każdy losuje w losowej kolejności, aż dostanie wynik."""
    order = participants[:]
    rng.shuffle(order)
    for me in order:
        attempts = 0
        while not me["result"]:
            perform_draw(participants, me, rng)
            attempts += 1
            assert attempts <= 2, "więcej niż jedna dodatkowa próba"


@pytest.mark.parametrize("n", [2, 3, 4, 5, 8, 15])
def test_full_draw_is_always_valid(n):
    rng = random.Random(n)
    for _ in range(2000):
        people = make_participants(n)
        run_full_draw(people, rng)
        results = [p["result"] for p in people]
        assert sorted(results) == sorted(p["name"] for p in people), "każdy wylosowany dokładnie raz"
        assert all(p["result"] != p["name"] for p in people), "nikt nie ma siebie"


def test_self_hit_happens_and_second_try_excludes_self():
    people = make_participants(5)
    me = people[0]
    assert me["name"] in candidates_for(people, me)  # pierwsza próba – można trafić siebie

    class AlwaysMe(random.Random):
        def choice(self, seq):
            return me["name"] if me["name"] in seq else seq[0]

    assert perform_draw(people, me, AlwaysMe())["status"] == "self"
    assert me["self_hit"] and me["result"] is None
    assert me["name"] not in candidates_for(people, me)
    outcome = perform_draw(people, me, AlwaysMe())
    assert outcome["status"] == "ok" and outcome["result"] != me["name"]


def test_drawing_again_returns_same_result():
    people = make_participants(4)
    rng = random.Random(1)
    me = people[0]
    while not me["result"]:
        perform_draw(people, me, rng)
    first = me["result"]
    assert perform_draw(people, me, rng) == {"status": "ok", "result": first, "already": True}


# ---------- API ----------

STORES = ["json"] + (["postgres"] if os.environ.get("TEST_DATABASE_URL") else [])


@pytest.fixture(params=STORES)
def store(request, tmp_path):
    if request.param == "json":
        return JsonStore(tmp_path / "stan.json")
    s = PostgresStore(os.environ["TEST_DATABASE_URL"])
    with s._connect() as conn:
        conn.execute(f"DELETE FROM {s.TABLE}")
    return s


@pytest.fixture
def client(store):
    store.save({
        "admin_token": "ADMIN",
        "deadline": (now() + timedelta(hours=1)).isoformat(),
        "participants": make_participants(4),
    })
    app = create_app(store, setup_key="KLUCZ")
    app.config["TESTING"] = True
    return app.test_client(), store


def test_pages_render(client):
    c, _ = client
    assert c.get("/").status_code == 200
    assert c.get("/l/t0").status_code == 200
    assert c.get("/l/zly").status_code == 404
    assert c.get("/admin/ADMIN").status_code == 200
    assert c.get("/admin/zly").status_code == 404


def test_api_full_flow(client):
    c, store = client
    for i in range(4):
        while True:
            r = c.post(f"/api/draw/t{i}").get_json()
            if r["status"] == "ok":
                break
    results = [p["result"] for p in store.load()["participants"]]
    assert sorted(results) == [f"Osoba{i}" for i in range(4)]


def test_api_closed_after_deadline(client):
    c, store = client
    state = store.load()
    state["deadline"] = (now() - timedelta(minutes=1)).isoformat()
    store.save(state)
    assert c.post("/api/draw/t0").status_code == 410


def test_admin_reset(client):
    c, store = client
    c.post("/api/draw/t0")
    c.post("/admin/ADMIN/reset")
    assert all(p["result"] is None for p in store.load()["participants"])


def test_setup_page(client):
    c, store = client
    future = (now() + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M")
    form = {"key": "KLUCZ", "names": "Ala\nOla\nEla", "deadline": future}

    assert c.get("/setup").status_code == 200
    assert c.post("/setup", data={**form, "key": "zle"}).status_code == 400
    assert c.post("/setup", data=form).status_code == 400  # istnieje, brak „nadpisz”
    assert c.post("/setup", data={**form, "names": "Ala\nAla", "overwrite": "1"}).status_code == 400

    r = c.post("/setup", data={**form, "overwrite": "1"})
    assert r.status_code == 302
    state = store.load()
    assert [p["name"] for p in state["participants"]] == ["Ala", "Ola", "Ela"]
    assert state["admin_token"] in r.headers["Location"]
    assert c.get(r.headers["Location"]).status_code == 200


def test_setup_disabled_without_key(store):
    app = create_app(store, setup_key="")
    assert app.test_client().get("/setup").status_code == 404


def test_not_configured(store):
    c = create_app(store, setup_key="KLUCZ").test_client()
    assert c.get("/").status_code == 503
    assert c.post("/api/draw/t0").status_code == 503
    with pytest.raises(StateMissing):
        store.load()


def test_concurrent_draws_never_collide(client):
    """Wszyscy klikają naraz – nikt nie może wylosować tej samej osoby."""
    from concurrent.futures import ThreadPoolExecutor

    c, store = client

    def draw_until_done(i):
        while c.post(f"/api/draw/t{i}").get_json()["status"] != "ok":
            pass

    with ThreadPoolExecutor(4) as pool:
        list(pool.map(draw_until_done, range(4)))
    results = [p["result"] for p in store.load()["participants"]]
    assert sorted(results) == [f"Osoba{i}" for i in range(4)]
