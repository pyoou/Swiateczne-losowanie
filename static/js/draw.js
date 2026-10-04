// Przebieg losowania: prezent → bęben z imionami → wynik.
(() => {
  const data = JSON.parse(document.getElementById("draw-data").textContent);
  const $ = (id) => document.getElementById(id);

  const giftArea = $("gift-area");
  const gift = $("gift");
  const drawBtn = $("draw-btn");
  const reel = $("reel");
  const strip = $("reel-strip");
  const selfHit = $("self-hit");
  const redrawBtn = $("redraw-btn");
  const result = $("result");
  const resultCard = $("result-card");
  const resultName = $("result-name");
  const hideBtn = $("hide-btn");
  const closed = $("closed");
  const errorBox = $("error");
  const lead = $("lead");
  const soundToggle = $("sound-toggle");

  const SPIN_MS = 5200;
  const FILLER_COUNT = 46;
  const wait = (ms) => new Promise((r) => setTimeout(r, ms));
  let busy = false;

  // ---------- widoki ----------
  function show(el) {
    for (const v of [giftArea, reel, selfHit, result, closed]) v.hidden = v !== el;
  }

  function showError(msg) {
    errorBox.textContent = msg;
    errorBox.hidden = false;
  }

  function showResult(name, celebrate) {
    resultName.textContent = name;
    result.classList.toggle("no-anim", !celebrate);
    show(result);
    lead.textContent = "Losowanie zakończone – teraz tylko znaleźć idealny prezent! 🎄";
    if (celebrate) {
      window.confettiBurst?.();
      setTimeout(() => window.confettiBurst?.(120), 700);
      window.sound.fanfare();
    }
  }

  function showSelfHit(animate) {
    show(selfHit);
    lead.textContent = "Ups! Zdarza się najlepszym 😄";
    if (animate) window.sound.oops();
  }

  // ---------- bęben ----------
  function buildStrip(target) {
    const others = data.names.filter((n) => n !== target);
    const pool = others.length ? others : [target];
    const items = [];
    let prev = null;
    for (let i = 0; i < FILLER_COUNT; i++) {
      let n;
      do { n = pool[Math.floor(Math.random() * pool.length)]; } while (pool.length > 1 && n === prev);
      items.push(n);
      prev = n;
    }
    items.push(target);
    items.push(pool[Math.floor(Math.random() * pool.length)]); // sąsiad poniżej wyniku
    strip.replaceChildren(...items.map((n) => {
      const li = document.createElement("li");
      li.textContent = n;
      return li;
    }));
    return items.length - 2; // indeks wylosowanej osoby
  }

  function spinTo(target) {
    return new Promise((resolve) => {
      const targetIndex = buildStrip(target);
      const winner = strip.children[targetIndex];
      // Wymiary z układu strony (offset*/client*), NIE z getBoundingClientRect –
      // ta uwzględnia animację powiększania bębna (scale 0.85 → 1) i zaniża wynik,
      // przez co bęben zatrzymywał się na złym imieniu.
      const itemH = winner.offsetHeight;
      const windowH = strip.parentElement.clientHeight;
      // Środek wylosowanego imienia ma wypaść dokładnie na środku okienka.
      const finalY = -(winner.offsetTop + itemH / 2 - windowH / 2);

      strip.style.transition = "none";
      strip.style.transform = "translateY(0)";
      void strip.offsetHeight; // wymuś przeliczenie, żeby animacja ruszyła od zera
      strip.style.transition = `transform ${SPIN_MS}ms cubic-bezier(0.12, 0.75, 0.16, 1)`;
      strip.style.transform = `translateY(${finalY}px)`;

      // „Tykanie” przy każdym przeskoku imienia.
      let lastIdx = 0;
      let done = false;
      (function tickLoop() {
        if (done) return;
        const y = new DOMMatrixReadOnly(getComputedStyle(strip).transform).m42;
        const idx = Math.floor(-y / itemH);
        if (idx !== lastIdx) { window.sound.tick(); lastIdx = idx; }
        requestAnimationFrame(tickLoop);
      })();

      const finish = () => {
        if (done) return;
        done = true;
        winner.classList.add("winner");
        resolve();
      };
      strip.addEventListener("transitionend", finish, { once: true });
      setTimeout(finish, SPIN_MS + 300);
    });
  }

  // ---------- komunikacja z serwerem ----------
  async function requestDraw() {
    const res = await fetch(data.drawUrl, { method: "POST", headers: { Accept: "application/json" } });
    let json = {};
    try { json = await res.json(); } catch (_) {}
    if (!res.ok) throw new Error(json.error || "Coś poszło nie tak. Spróbuj odświeżyć stronę.");
    return json;
  }

  async function run({ fromGift }) {
    if (busy) return;
    busy = true;
    errorBox.hidden = true;
    drawBtn.disabled = redrawBtn.disabled = true;
    window.sound.unlock();

    if (fromGift) gift.classList.add("shake");
    let outcome;
    try {
      [outcome] = await Promise.all([requestDraw(), wait(fromGift ? 1100 : 200)]);
    } catch (e) {
      gift.classList.remove("shake");
      showError(e.message);
      drawBtn.disabled = redrawBtn.disabled = false;
      busy = false;
      return;
    }

    if (fromGift) {
      gift.classList.remove("shake");
      gift.classList.add("open");
      window.confettiBurst?.(40);
      await wait(650);
    }

    show(reel);
    lead.textContent = "Bęben się kręci… 🥁";
    const target = outcome.status === "self" ? data.me : outcome.result;
    await spinTo(target);
    await wait(900);

    if (outcome.status === "self") showSelfHit(true);
    else showResult(outcome.result, true);

    redrawBtn.disabled = false;
    busy = false;
  }

  // ---------- zdarzenia ----------
  gift.addEventListener("click", () => run({ fromGift: true }));
  drawBtn.addEventListener("click", () => run({ fromGift: true }));
  redrawBtn.addEventListener("click", () => run({ fromGift: false }));

  hideBtn.addEventListener("click", () => {
    const hidden = resultCard.classList.toggle("hidden-name");
    hideBtn.textContent = hidden ? "👀 Pokaż" : "🙈 Ukryj";
  });

  if (soundToggle) {
    const render = () => {
      soundToggle.textContent = window.sound.enabled ? "🔊" : "🔇";
      soundToggle.setAttribute("aria-pressed", String(window.sound.enabled));
    };
    soundToggle.addEventListener("click", () => { window.sound.toggle(); render(); });
    render();
  }

  // ---------- stan początkowy (np. po odświeżeniu strony) ----------
  if (data.result) {
    lead.textContent = "Już losowałeś/aś – oto Twój wynik:";
    showResult(data.result, false);
  } else if (data.closed) {
    show(closed);
  } else if (data.pendingRedraw) {
    showSelfHit(false);
  } else {
    show(giftArea);
  }
})();
