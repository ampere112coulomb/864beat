(() => {
  'use strict';
  const canvas = document.querySelector('.game-particles');
  if (!canvas) return;
  const context = canvas.getContext('2d');
  if (!context) return;
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const started = performance.now();
  let width = 1, height = 1, frame = 0, previous = -Infinity;
  // Pre-render two soft sprites rather than rebuilding gradients each frame.
  const sprites = [[130, 205, 240], [185, 150, 240]].map(rgb => {
    const sprite = document.createElement('canvas');
    sprite.width = sprite.height = 64;
    const g = sprite.getContext('2d');
    const gradient = g.createRadialGradient(32, 32, 0, 32, 32, 32);
    gradient.addColorStop(0, `rgba(${rgb},1)`);
    gradient.addColorStop(.33, `rgba(${rgb},.16)`);
    gradient.addColorStop(1, `rgba(${rgb},0)`);
    g.fillStyle = gradient;
    g.fillRect(0, 0, 64, 64);
    return sprite;
  });
  function draw(now) {
    context.clearRect(0, 0, width, height);
    const time = reducedMotion.matches ? 0 : (now - started) / 1000;
    for (let i = 0; i < 48; i++) {
      const duration = 16 + (i * 17 % 15);
      const age = (time / duration + i * .61803398875) % 1;
      const wave = time * (.55 + i % 5 * .065) + i * 2.399963;
      const anchor = (i * .7548776662) % 1;
      const x = width * (.025 + .95 * anchor) + Math.sin(wave) * width * (.009 + i % 4 * .003);
      const y = height * (1.04 - age * 1.12);
      const radius = Math.max(.6, height / 1080) * (1.3 + i % 5 * .4);
      const fade = Math.max(0, Math.min(1, age / .12, (1 - age) / .18));
      context.globalAlpha = (95 / 255) * fade * (.8 + .2 * Math.sin(wave * .7));
      context.drawImage(sprites[i % 3 === 0 ? 0 : 1], x - radius * 3, y - radius * 3, radius * 6, radius * 6);
    }
    context.globalAlpha = 1;
  }
  function tick(now) {
    frame = 0;
    if (document.hidden || reducedMotion.matches) return;
    if (now - previous >= 1000 / 30) { draw(now); previous = now; }
    frame = requestAnimationFrame(tick);
  }
  function update() {
    cancelAnimationFrame(frame); frame = 0;
    if (document.hidden) return;
    draw(performance.now()); previous = -Infinity;
    if (!reducedMotion.matches) frame = requestAnimationFrame(tick);
  }
  function resize() {
    width = innerWidth; height = innerHeight;
    const scale = Math.min(devicePixelRatio || 1, 1.5);
    canvas.width = Math.round(width * scale); canvas.height = Math.round(height * scale);
    context.setTransform(scale, 0, 0, scale, 0, 0);
    update();
  }
  addEventListener('resize', resize, { passive: true });
  document.addEventListener('visibilitychange', update);
  reducedMotion.addEventListener('change', update);
  resize();
})();
