// The hero mark's animation, against the BUILT site.
//
// Everything here is a claim that cannot be settled by reading the output: that
// the first frame reproduces what the build drew, that reduced motion leaves
// the mark alone, that scrolling away stops the work. The first of those is the
// one most likely to catch a real defect, because no single phase of the sweep
// reproduces the resting pose and an animation that simply starts would snap.
const { test, expect } = require("@playwright/test");

const SELECTOR = "[data-mark-animation]";

// Compare two path strings as the POINTS they draw.
//
// The built page is minified, so its path data has been rewritten into relative
// commands and axis shorthands while the script writes plain absolute ones. The
// same curve in two notations has to compare equal, so the commands are applied
// rather than the text compared.
//
// The comparison is exact. Both producers round to one decimal, so identical
// arithmetic gives identical strings, and any tolerance at all hides the thing
// this is looking for: an earlier version of this test resampled both paths by
// arc length and could not see the script using a different number of samples
// for the nesting scale, because the resampling smoothed the difference away.
const TOKEN = /([MmLlHhVvZz])|(-?(?:\d+\.\d+|\d+|\.\d+)(?:[eE][+-]?\d+)?)/g;

function points(d) {
  const pts = [];
  let x = 0;
  let y = 0;
  let cmd = null;
  let nums = [];
  const flush = () => {
    if (cmd === null) {
      nums = [];
      return;
    }
    if ("HhVv".includes(cmd)) {
      for (const n of nums) {
        if (cmd === "H") x = n;
        else if (cmd === "h") x += n;
        else if (cmd === "V") y = n;
        else y += n;
        pts.push([round1(x), round1(y)]);
      }
    } else {
      for (let i = 0; i + 1 < nums.length; i += 2) {
        if (cmd === "m" || cmd === "l") {
          x += nums[i];
          y += nums[i + 1];
        } else {
          x = nums[i];
          y = nums[i + 1];
        }
        pts.push([round1(x), round1(y)]);
      }
    }
    nums = [];
  };
  for (const m of d.matchAll(TOKEN)) {
    if (m[1]) {
      flush();
      cmd = "Zz".includes(m[1]) ? null : m[1];
    } else {
      nums.push(parseFloat(m[2]));
    }
  }
  flush();
  return pts;
}

// Accumulated relative segments land a hair off an exact tenth, so the value is
// snapped back before comparison. This is rounding, not tolerance: anything
// further than half a tenth away still compares unequal.
function round1(v) {
  const r = Math.round(v * 10) / 10;
  return r === 0 ? 0 : r;
}

function sameShape(a, b, label) {
  const pa = points(a);
  const pb = points(b);
  expect(pb.length, `${label}: point count`).toBe(pa.length);
  const differ = pa.findIndex((q, i) => q[0] !== pb[i][0] || q[1] !== pb[i][1]);
  expect(
    differ,
    differ === -1
      ? ""
      : `${label}: point ${differ} is ${JSON.stringify(pb[differ])}, ` +
        `the build drew ${JSON.stringify(pa[differ])}`
  ).toBe(-1);
}

async function builtPaths(browser) {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto("/");
  const d = await page.$$eval(`${SELECTOR} path`, (ps) =>
    ps.map((p) => ({ d: p.getAttribute("d"), fill: p.getAttribute("fill") }))
  );
  await context.close();
  return d;
}

test("the mark the build drew is the mark a reader without scripting sees", async ({
  browser,
}) => {
  const built = await builtPaths(browser);
  expect(built.length, "the hero mark must be generated at build time").toBeGreaterThan(1);
  for (const p of built) {
    expect(p.d, "every copy carries generated path data").toMatch(/^[Mm]/);
    expect(p.fill, "every fill is a ramp step, never a colour value").toMatch(
      /^var\(--mark-ramp-\d+\)$/
    );
  }
});

test("the first frame the script draws is the shape the build rendered", async ({
  browser,
}) => {
  const built = await builtPaths(browser);

  const context = await browser.newContext();
  // Installed before any page script, so it sees the very first write. Reading
  // the attribute later would compare against a frame the animation has already
  // moved on from, which is exactly the defect this is looking for.
  await context.addInitScript(() => {
    window.__first = new Map();
    new MutationObserver((records) => {
      for (const r of records) {
        if (r.attributeName === "d" && !window.__first.has(r.target)) {
          window.__first.set(r.target, r.target.getAttribute("d"));
        }
      }
      // Observing `document` rather than `document.documentElement`: this runs
      // before the page's own document exists, and the element reference would
      // be the blank one the parser then replaces, so nothing would be seen.
    }).observe(document, {
      subtree: true,
      attributes: true,
      attributeFilter: ["d"],
    });
  });
  const page = await context.newPage();
  await page.goto("/");
  await page.waitForFunction(() => window.__first && window.__first.size > 0);
  const first = await page.evaluate(() => [...window.__first.values()]);

  expect(first.length, "the script must redraw every copy the build drew").toBe(built.length);
  for (let i = 0; i < built.length; i++) {
    sameShape(built[i].d, first[i], `copy ${i}`);
  }
  await context.close();
});

test("reduced motion leaves the built mark untouched", async ({ browser }) => {
  const built = await builtPaths(browser);

  const context = await browser.newContext({ reducedMotion: "reduce" });
  const page = await context.newPage();
  await page.goto("/");
  const read = () =>
    page.$$eval(`${SELECTOR} path`, (ps) => ps.map((p) => p.getAttribute("d")));

  const before = await read();
  await page.waitForTimeout(1000);
  const after = await read();

  expect(after, "nothing may be redrawn under reduced motion").toEqual(before);
  expect(
    after,
    "and what stands is the build's own path data, byte for byte"
  ).toEqual(built.map((p) => p.d));
  await context.close();
});

test("the animation stops off-screen and resumes on return", async ({ browser }) => {
  const context = await browser.newContext();
  await context.addInitScript(() => {
    window.__frames = 0;
    const raf = window.requestAnimationFrame.bind(window);
    window.requestAnimationFrame = function (cb) {
      return raf(function (t) {
        window.__frames++;
        return cb(t);
      });
    };
  });
  const page = await context.newPage();
  await page.goto("/");
  await page.waitForFunction(() => window.__frames > 2);

  await page.evaluate(() => {
    document.querySelector("[data-mark-animation]").scrollIntoView();
    window.scrollBy(0, window.innerHeight * 3);
  });
  // The observer fires asynchronously; give it a frame or two to take effect
  // before the count is treated as settled.
  await page.waitForTimeout(400);
  const settled = await page.evaluate(() => window.__frames);
  await page.waitForTimeout(600);
  const later = await page.evaluate(() => window.__frames);
  expect(later, "an off-screen animation must not keep drawing").toBe(settled);

  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(400);
  const back = await page.evaluate(() => window.__frames);
  expect(back, "and must resume when it is visible again").toBeGreaterThan(later);
  await context.close();
});

test("the copies stay nested for the whole sweep", async ({ page }) => {
  await page.goto("/");
  const cfg = JSON.parse(
    await page.getAttribute(SELECTOR, "data-mark-animation")
  );

  // Sampled across the cycle rather than at one moment: the nesting scale
  // depends on the rotation as well as the shape, so a breach would appear at
  // one phase and not another.
  for (let i = 0; i < 8; i++) {
    await page.waitForTimeout(250);
    const frame = await page.$$eval(`${SELECTOR} path`, (ps) =>
      ps
        .filter((p) => p.getAttribute("display") !== "none")
        .map((p) => {
          const b = p.getBBox();
          return {
            extent: Math.max(
              Math.abs(b.x),
              Math.abs(b.y),
              Math.abs(b.x + b.width),
              Math.abs(b.y + b.height)
            ),
            fill: p.getAttribute("fill"),
          };
        })
    );
    expect(frame.length, "copy count stays within its declared range").toBeGreaterThanOrEqual(
      cfg.range.copies[0]
    );
    expect(frame.length).toBeLessThanOrEqual(cfg.range.copies[1]);
    for (let j = 1; j < frame.length; j++) {
      expect(
        frame[j].extent,
        `sample ${i}: copy ${j} is larger than copy ${j - 1}, so the nesting has inverted`
      ).toBeLessThanOrEqual(frame[j - 1].extent + 0.5);
    }
    for (const p of frame) {
      const m = /^var\(--mark-ramp-(\d+)\)$/.exec(p.fill);
      expect(m, `sample ${i}: fill ${p.fill} is not a ramp step`).not.toBeNull();
      expect(Number(m[1])).toBeLessThanOrEqual(cfg.rampSteps);
    }
  }
});

test("a frame costs less than a frame budget on a throttled processor", async ({ page }) => {
  await page.goto("/");
  const cdp = await page.context().newCDPSession(page);
  const cfg = JSON.parse(
    await page.getAttribute(SELECTOR, "data-mark-animation")
  );

  // 6x is a mid-range phone against this machine. The animation is the site's
  // only continuous work, so if it does not fit here it drops frames for a
  // reader who cannot do anything about it.
  await cdp.send("Emulation.setCPUThrottlingRate", { rate: 6 });
  const cost = await page.evaluate((c) => {
    // The hot path, reconstructed from the same data the script reads, so this
    // measures the real cost rather than a guess at it.
    const R = (a, t) => a + Math.cos(3 * t);
    const fit = (a, phi) => {
      let m = Infinity;
      for (let i = 0; i < c.fitSamples; i++) {
        const t = (2 * Math.PI * i) / c.fitSamples;
        const ch = R(a, t - phi);
        if (ch > 0.0001) m = Math.min(m, R(a, t) / ch);
      }
      return m;
    };
    const times = [];
    for (let f = 0; f < 120; f++) {
      const ph = 0.5 - 0.5 * Math.cos((f / 60) * 2 * Math.PI);
      const a = c.range.ratio[0] + (c.range.ratio[1] - c.range.ratio[0]) * ph;
      const rot = c.range.rot[0] + (c.range.rot[1] - c.range.rot[0]) * ph;
      const ft = c.range.fit[0] + (c.range.fit[1] - c.range.fit[0]) * ph;
      const t0 = performance.now();
      const phi = (rot * Math.PI) / 180;
      const step = Math.pow(fit(a, phi), 1 - 5 * ft);
      const scale = 170 / (a + 1);
      for (let i = 0; i < c.maxCopies; i++) {
        const s = scale * Math.pow(step, i);
        let d = "";
        for (let k = 0; k <= c.points; k++) {
          const t = (2 * Math.PI * k) / c.points;
          const h = R(a, t);
          d +=
            (k ? "L" : "M") +
            (s * h * Math.cos(t + phi * i)).toFixed(1) +
            " " +
            (-(s * h * Math.sin(t + phi * i))).toFixed(1);
        }
        if (d.length < 0) throw new Error("unreachable");
      }
      times.push(performance.now() - t0);
    }
    times.sort((x, y) => x - y);
    return { median: times[60], p95: times[114], worst: times[119] };
  }, cfg);
  await cdp.send("Emulation.setCPUThrottlingRate", { rate: 1 });

  console.log(
    `  mark frame at 6x: median ${cost.median.toFixed(2)}ms ` +
      `p95 ${cost.p95.toFixed(2)}ms worst ${cost.worst.toFixed(2)}ms`
  );
  expect(cost.p95, "p95 frame cost at 6x throttling").toBeLessThan(16.7);
});
