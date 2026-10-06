---
# nivistf-7z1r
title: the big logo in the hero, should be an animation
status: draft
type: task
priority: normal
created_at: 2026-10-06T15:24:27Z
updated_at: 2026-10-06T15:50:41Z
openspec-link: x
---

try this:

```
<div id="nivis-mark" style="max-width:480px"></div>
<script>
(function nivisMarkRuntime(cfg) {
  var NS = 'http://www.w3.org/2000/svg';
  var FIT_AGGRESSIVENESS = 5, BASE_HUE = 205, STEPS = 360, MAX_COPIES = 12;

  var host = typeof cfg.target === 'string' ? document.querySelector(cfg.target) : cfg.target;
  if (!host) { console.warn('Nivis mark: target element not found'); return null; }

  var svg = document.createElementNS(NS, 'svg');
  svg.setAttribute('viewBox', '0 0 400 400');
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', cfg.label || 'Nivis mark');
  svg.setAttribute('shape-rendering', 'geometricPrecision');
  svg.style.cssText = 'display:block;width:100%;height:auto';
  if (cfg.background) {
    var bg = document.createElementNS(NS, 'rect');
    bg.setAttribute('width', '400');
    bg.setAttribute('height', '400');
    bg.setAttribute('fill', cfg.background);
    svg.appendChild(bg);
  }
  var pool = [];
  for (var p = 0; p <= MAX_COPIES; p++) {
    var path = document.createElementNS(NS, 'path');
    path.setAttribute('display', 'none');
    svg.appendChild(path);
    pool.push(path);
  }
  host.appendChild(svg);

  function ratioAt(a, phi, t) {
    var child = a + Math.cos(3 * (t - phi));
    return child > 1e-6 ? (a + Math.cos(3 * t)) / child : Infinity;
  }
  function perfectFit(a, phi) {
    var N = 360, best = Infinity, bestI = 0, i;
    for (i = 0; i < N; i++) {
      var r = ratioAt(a, phi, (i / N) * 2 * Math.PI);
      if (r < best) { best = r; bestI = i; }
    }
    var lo = ((bestI - 1) / N) * 2 * Math.PI, hi = ((bestI + 1) / N) * 2 * Math.PI;
    for (i = 0; i < 40; i++) {
      var m1 = lo + (hi - lo) / 3, m2 = hi - (hi - lo) / 3;
      if (ratioAt(a, phi, m1) < ratioAt(a, phi, m2)) hi = m2; else lo = m1;
    }
    return Math.min(best, ratioAt(a, phi, (lo + hi) / 2));
  }
  function shapePath(a, rot, s) {
    var d = '';
    for (var k = 0; k <= STEPS; k++) {
      var t = (k / STEPS) * 2 * Math.PI, h = a + Math.cos(3 * t);
      d += (k ? 'L' : 'M') + (200 + s * h * Math.cos(t + rot)).toFixed(3) + ',' + (200 - s * h * Math.sin(t + rot)).toFixed(3);
    }
    return d + 'Z';
  }
  function color(name, i, n) {
    var t = n > 1 ? Math.min(1, Math.max(0, i / (n - 1))) : 0, hue;
    if (name === 'ink') return '#000';
    if (name === 'mono') return 'hsl(' + BASE_HUE + ',65%,' + (72 - t * 45) + '%)';
    switch (name) {
      case 'complementary': hue = i % 2 === 0 ? BASE_HUE : BASE_HUE + 180; break;
      case 'triadic':       hue = BASE_HUE + (i % 3) * 120; break;
      case 'warm':          hue = 10 + t * 45; break;
      case 'cool':          hue = 175 + t * 95; break;
      default:              hue = BASE_HUE + (t - 0.5) * 60;
    }
    return 'hsl(' + (((hue % 360) + 360) % 360) + ',65%,50%)';
  }
  function render(v) {
    var n = Math.min(MAX_COPIES, Math.max(1, v.n));
    var phi = v.rot * Math.PI / 180;
    var step = Math.pow(perfectFit(v.r, phi), 1 - FIT_AGGRESSIVENESS * v.fit);
    var scale = 170 / (v.r + 1), rot = 0;
    var whole = Math.floor(n + 1e-9), frac = n - whole;
    var drawn = frac > 1e-6 ? whole + 1 : whole;
    for (var i = 0; i < pool.length; i++) {
      var el = pool[i];
      if (i < drawn) {
        el.setAttribute('d', shapePath(v.r, rot, scale));
        el.setAttribute('fill', color(cfg.palette, i, n));
        el.setAttribute('fill-opacity', (v.op * (i === whole ? frac : 1)).toFixed(4));
        el.setAttribute('display', 'inline');
        scale *= step;
        rot += phi;
      } else {
        el.setAttribute('display', 'none');
      }
    }
  }

  var base = cfg.values, anim = cfg.animate || {}, keys = Object.keys(anim);
  var speed = cfg.speed || 1, cycle = cfg.cycleSeconds || 4;
  var v = {}, k0;
  for (k0 in base) v[k0] = base[k0];

  var running = false, raf = null, last = null, clock = 0, visible = true, paused = false;
  var mq = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;

  function frame(ts) {
    raf = null;
    if (!running) return;
    if (last === null) last = ts;
    clock += Math.min((ts - last) / 1000, 0.1) * speed;
    last = ts;
    var phase = 0.5 + 0.5 * Math.sin((clock / cycle) * 2 * Math.PI - Math.PI / 2);
    keys.forEach(function (k) { v[k] = anim[k][0] + (anim[k][1] - anim[k][0]) * phase; });
    render(v);
    raf = requestAnimationFrame(frame);
  }
  function update() {
    var reduced = mq && mq.matches;
    var should = keys.length > 0 && !paused && visible && !document.hidden && !reduced;
    if (should && !running) {
      running = true; last = null;
      raf = requestAnimationFrame(frame);
    } else if (!should && running) {
      running = false;
      if (raf) cancelAnimationFrame(raf);
      raf = null;
    }
    if (reduced || !keys.length) {
      for (var k in base) v[k] = base[k];
      render(v);
    }
  }

  render(v);
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (entries) { visible = entries[0].isIntersecting; update(); }).observe(host);
  }
  document.addEventListener('visibilitychange', update);
  if (mq) { if (mq.addEventListener) mq.addEventListener('change', update); else if (mq.addListener) mq.addListener(update); }
  update();

  return {
    play: function () { paused = false; update(); },
    pause: function () { paused = true; update(); }
  };
})({
  "target": "#nivis-mark",
  "label": "Nivis mark",
  "palette": "analogous",
  "background": null,
  "speed": 0.2,
  "cycleSeconds": 4,
  "values": {
    "r": 9.2435,
    "n": 3.6218,
    "rot": 19.461,
    "fit": -0.6108,
    "op": 0.2135
  },
  "animate": {
    "r": [
      6,
      16
    ],
    "n": [
      2,
      7
    ],
    "rot": [
      0,
      60
    ],
    "fit": [
      -1,
      0.2
    ],
    "op": [
      0.1,
      0.45
    ]
  }
});
</script>
```
