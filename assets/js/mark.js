(function () {
  var svg = document.querySelector("[data-mark-animation]");
  if (!svg) return;

  var cfg;
  try {
    cfg = JSON.parse(svg.getAttribute("data-mark-animation"));
  } catch (e) {
    return;
  }

  // The mark is already on the page, drawn by the build. Nothing here creates
  // an SVG or a first frame: with scripting unavailable, with reduced motion,
  // or off-screen, what stands is what the build rendered. That is why the
  // reduced-motion test can assert the path data is byte-identical rather than
  // merely similar.
  var mq = window.matchMedia
    ? window.matchMedia("(prefers-reduced-motion: reduce)")
    : null;

  var NS = "http://www.w3.org/2000/svg";
  var paths = [].slice.call(svg.querySelectorAll("path"));
  var rest = cfg.rest;
  var range = cfg.range;
  var keys = ["ratio", "copies", "rot", "fit", "opacity"];

  // The lobe count arrives as data like everything else, so the script cannot
  // disagree with the build about what shape it is drawing.
  function R(a, t) {
    return a + Math.cos(cfg.rest.lobes * t);
  }

  // The same minimisation the build performs, over the same sample count, which
  // arrives as data rather than being restated here. Two sample counts give
  // scales that differ in the last decimal, and the first frame has to
  // reproduce the built shape exactly.
  function perfectFit(a, phi) {
    var m = Infinity;
    for (var i = 0; i < cfg.fitSamples; i++) {
      var t = (2 * Math.PI * i) / cfg.fitSamples;
      var child = R(a, t - phi);
      if (child > 0.0001) {
        var r = R(a, t) / child;
        if (r < m) m = r;
      }
    }
    return m;
  }

  function tone(i, n) {
    var t = n > 1 ? Math.round((cfg.rampSteps * i) / (n - 1)) : 0;
    return t < 0 ? 0 : t > cfg.rampSteps ? cfg.rampSteps : t;
  }

  function draw(v) {
    var phi = (v.rot * Math.PI) / 180;
    var step = Math.pow(perfectFit(v.ratio, phi), 1 - 5 * v.fit);
    var scale = 170 / (v.ratio + 1);
    var whole = Math.floor(v.copies + 1e-9);
    var frac = v.copies - whole;
    var drawn = frac > 1e-6 ? whole + 1 : whole;
    if (drawn > cfg.maxCopies) drawn = cfg.maxCopies;

    while (paths.length < drawn) {
      var p = document.createElementNS(NS, "path");
      svg.appendChild(p);
      paths.push(p);
    }

    for (var i = 0; i < paths.length; i++) {
      var el = paths[i];
      if (i >= drawn) {
        el.setAttribute("display", "none");
        continue;
      }
      var rot = phi * i;
      var s = scale * Math.pow(step, i);
      var d = "";
      for (var k = 0; k <= cfg.points; k++) {
        var t = (2 * Math.PI * k) / cfg.points;
        var h = R(v.ratio, t);
        d +=
          (k ? "L" : "M") +
          (s * h * Math.cos(t + rot)).toFixed(1) +
          " " +
          (-(s * h * Math.sin(t + rot))).toFixed(1);
      }
      el.setAttribute("d", d + "Z");
      el.setAttribute("fill", "var(--mark-ramp-" + tone(i, v.copies) + ")");
      el.setAttribute(
        "fill-opacity",
        (v.opacity * (i === whole ? frac : 1)).toFixed(3)
      );
      el.removeAttribute("display");
    }
  }

  var running = false;
  var raf = null;
  var last = null;
  var clock = 0;
  var onScreen = true;

  function frame(ts) {
    raf = null;
    if (!running) return;
    if (last === null) last = ts;
    // Capped, so a backgrounded tab that misses the visibility event does not
    // return and jump a second of animation in one step.
    clock += Math.min((ts - last) / 1000, 0.1);
    last = ts;

    // The sweep starts at the resting pose and opens out to its full range over
    // easeIn seconds. Without this the first frame would land wherever the
    // phase function starts, and the mark would snap the moment the script ran:
    // no single phase reproduces the resting pose, because each parameter sits
    // at a different fraction of its own range.
    var w = Math.min(1, clock / cfg.easeIn);
    var phase = 0.5 - 0.5 * Math.cos((clock / cfg.cycle) * 2 * Math.PI);
    var v = {};
    for (var i = 0; i < keys.length; i++) {
      var k = keys[i];
      var swept = range[k][0] + (range[k][1] - range[k][0]) * phase;
      v[k] = rest[k] + w * (swept - rest[k]);
    }
    draw(v);
    raf = requestAnimationFrame(frame);
  }

  function update() {
    var should = onScreen && !document.hidden && !(mq && mq.matches);
    if (should && !running) {
      running = true;
      last = null;
      raf = requestAnimationFrame(frame);
    } else if (!should && running) {
      running = false;
      if (raf) cancelAnimationFrame(raf);
      raf = null;
    }
  }

  if ("IntersectionObserver" in window) {
    new IntersectionObserver(function (entries) {
      onScreen = entries[0].isIntersecting;
      update();
    }).observe(svg);
  }
  document.addEventListener("visibilitychange", update);
  if (mq) {
    if (mq.addEventListener) mq.addEventListener("change", update);
    else if (mq.addListener) mq.addListener(update);
  }
  update();
})();
