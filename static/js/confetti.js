// Konfetti – window.confettiBurst() wystrzeliwuje salwę z dołu ekranu.
(() => {
  const canvas = document.getElementById("confetti");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const colors = ["#f6c86b", "#d7263d", "#2f9e63", "#ffffff", "#5cc8ff", "#ff7eb6"];
  const shapes = ["rect", "circle", "star"];
  let pieces = [];
  let running = false;

  function resize() {
    const dpr = window.devicePixelRatio || 1;
    canvas.width = window.innerWidth * dpr;
    canvas.height = window.innerHeight * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function drawStar(size) {
    ctx.beginPath();
    for (let i = 0; i < 5; i++) {
      const a = (i * 4 * Math.PI) / 5 - Math.PI / 2;
      ctx.lineTo(Math.cos(a) * size, Math.sin(a) * size);
    }
    ctx.closePath();
    ctx.fill();
  }

  function frame() {
    ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
    pieces = pieces.filter((p) => p.y < window.innerHeight + 40 && p.life > 0);
    for (const p of pieces) {
      p.vy += 0.18;
      p.vx *= 0.99;
      p.vy *= 0.99;
      p.x += p.vx;
      p.y += p.vy;
      p.rot += p.vr;
      p.life -= 1;
      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate(p.rot);
      ctx.globalAlpha = Math.min(1, p.life / 40);
      ctx.fillStyle = p.color;
      if (p.shape === "rect") ctx.fillRect(-p.size / 2, -p.size / 4, p.size, p.size / 2);
      else if (p.shape === "circle") { ctx.beginPath(); ctx.arc(0, 0, p.size / 3, 0, Math.PI * 2); ctx.fill(); }
      else drawStar(p.size / 2);
      ctx.restore();
    }
    if (pieces.length) requestAnimationFrame(frame);
    else running = false;
  }

  window.confettiBurst = function (amount = 180) {
    const w = window.innerWidth;
    const h = window.innerHeight;
    for (let i = 0; i < amount; i++) {
      const fromLeft = i % 2 === 0;
      pieces.push({
        x: fromLeft ? w * 0.1 : w * 0.9,
        y: h + 10,
        vx: (fromLeft ? 1 : -1) * (Math.random() * 7 + 2),
        vy: -(Math.random() * 12 + 10),
        size: Math.random() * 10 + 6,
        rot: Math.random() * Math.PI,
        vr: (Math.random() - 0.5) * 0.3,
        color: colors[Math.floor(Math.random() * colors.length)],
        shape: shapes[Math.floor(Math.random() * shapes.length)],
        life: 260 + Math.random() * 80,
      });
    }
    if (!running) {
      running = true;
      requestAnimationFrame(frame);
    }
  };

  window.addEventListener("resize", resize);
  resize();
})();
