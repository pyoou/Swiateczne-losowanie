// Padający śnieg w tle (canvas).
(() => {
  const canvas = document.getElementById("snow");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let flakes = [];
  let w, h, dpr;

  function resize() {
    dpr = window.devicePixelRatio || 1;
    w = window.innerWidth;
    h = window.innerHeight;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const count = Math.round((w * h) / (reduced ? 40000 : 9000));
    flakes = Array.from({ length: count }, () => makeFlake(true));
  }

  function makeFlake(anywhere) {
    const r = Math.random() * 2.6 + 0.8;
    return {
      x: Math.random() * w,
      y: anywhere ? Math.random() * h : -10,
      r,
      speed: r * 0.35 + Math.random() * 0.4,
      drift: Math.random() * Math.PI * 2,
      alpha: Math.random() * 0.5 + 0.4,
    };
  }

  function frame() {
    ctx.clearRect(0, 0, w, h);
    for (const f of flakes) {
      f.drift += 0.01;
      f.y += reduced ? f.speed * 0.3 : f.speed;
      f.x += Math.sin(f.drift) * 0.4;
      if (f.y > h + 10) Object.assign(f, makeFlake(false));
      ctx.beginPath();
      ctx.arc(f.x, f.y, f.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255,255,255,${f.alpha})`;
      ctx.fill();
    }
    requestAnimationFrame(frame);
  }

  window.addEventListener("resize", resize);
  resize();
  requestAnimationFrame(frame);
})();
