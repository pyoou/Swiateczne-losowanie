// Dźwięki generowane w przeglądarce (Web Audio) – bez plików mp3.
window.sound = (() => {
  const KEY = "losowanie-dzwiek";
  let ctx = null;
  let enabled = true;
  try { enabled = localStorage.getItem(KEY) !== "off"; } catch (_) {}

  function audio() {
    if (!enabled) return null;
    if (!ctx) {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return null;
      ctx = new AC();
    }
    if (ctx.state === "suspended") ctx.resume();
    return ctx;
  }

  function note(freq, start, duration, type = "sine", volume = 0.15) {
    const a = audio();
    if (!a) return;
    const t = a.currentTime + start;
    const osc = a.createOscillator();
    const gain = a.createGain();
    osc.type = type;
    osc.frequency.value = freq;
    gain.gain.setValueAtTime(0, t);
    gain.gain.linearRampToValueAtTime(volume, t + 0.01);
    gain.gain.exponentialRampToValueAtTime(0.0001, t + duration);
    osc.connect(gain).connect(a.destination);
    osc.start(t);
    osc.stop(t + duration + 0.05);
  }

  return {
    get enabled() { return enabled; },
    toggle() {
      enabled = !enabled;
      try { localStorage.setItem(KEY, enabled ? "on" : "off"); } catch (_) {}
      return enabled;
    },
    unlock() { audio(); },
    tick() { note(1400, 0, 0.04, "square", 0.04); },
    // Dzwoneczki: fragment „Jingle Bells” (E E E, E E E, E G C D E)
    fanfare() {
      const E = 659.25, G = 783.99, C = 523.25, D = 587.33;
      const seq = [E, E, E, null, E, E, E, null, E, G, C, D, E];
      seq.forEach((f, i) => f && note(f, i * 0.13, 0.35, "triangle", 0.18));
      note(E * 2, 13 * 0.13, 0.8, "sine", 0.08);
    },
    oops() {
      note(392, 0, 0.25, "sawtooth", 0.06);
      note(311, 0.22, 0.45, "sawtooth", 0.06);
    },
  };
})();
