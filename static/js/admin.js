// Panel organizatora: kopiowanie linków.
(() => {
  const people = JSON.parse(document.getElementById("people-data").textContent);

  async function copy(text, button) {
    try {
      await navigator.clipboard.writeText(text);
    } catch (_) {
      // Fallback dla http:// (bez https schowek bywa niedostępny)
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      ta.remove();
    }
    const original = button.textContent;
    button.textContent = "✅ Skopiowano!";
    setTimeout(() => (button.textContent = original), 1500);
  }

  document.querySelectorAll("[data-copy]").forEach((btn) =>
    btn.addEventListener("click", () => copy(btn.dataset.copy, btn))
  );

  document.querySelectorAll(".person-link").forEach((input) =>
    input.addEventListener("focus", () => input.select())
  );

  document.getElementById("copy-all").addEventListener("click", (e) => {
    const lines = people.map((p) => `🎁 ${p.name}: ${p.link}`);
    const message = [
      "🎄 Świąteczne losowanie prezentów! 🎄",
      "Każdy ma swój osobisty link – kliknij TYLKO swój i losuj:",
      "",
      ...lines,
      "",
      "Kogo wylosujesz, zachowaj w tajemnicy 🤫",
    ].join("\n");
    copy(message, e.currentTarget);
  });
})();
