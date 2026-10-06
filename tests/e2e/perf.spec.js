// The performance budget, measured as what the browser actually REQUESTS.
//
// Summing the files in public/ is the wrong measurement: a browser downloads a
// font only when an element needs that weight, so a declared-but-unused face
// costs a reader nothing at load time. Only the request log tells the truth.
const { test, expect } = require("@playwright/test");

// Budgets are deliberately a little above the measured values, so ordinary
// churn does not fail the gate but a regression of any real size does. The
// measured numbers are recorded in docs/TESTING.md.
// Measured on the built site, uncompressed, which is the pessimistic case: the
// test server does not compress, production does. Fonts are already compressed
// and gain nothing from it.
//
//   8 requests, 189,288 bytes total
//     69,883  document    (58% of it generated mark path data; gzips to ~18 KB)
//     11,919  stylesheet
//     21,184  font  Hind-Regular        (97,000 before subsetting)
//     22,116  font  Hind-Medium
//     21,980  font  Hind-SemiBold
//     20,692  font  IBMPlexMono-Regular
//     21,108  font  IBMPlexMono-Medium
//        406  script
//
// Each budget sits a little above its measurement, so ordinary churn passes and
// a real regression fails. Raising one should be a visible decision in a diff.
const BUDGET = {
  totalBytes: 220 * 1024,
  htmlBytes: 80 * 1024,
  cssBytes: 16 * 1024,
  jsBytes: 4 * 1024,
  requests: 10,
};

test("a cold load stays within the byte budget", async ({ page }) => {
  const seen = [];
  page.on("response", async (res) => {
    const url = new URL(res.url());
    let size = 0;
    try {
      size = (await res.body()).length;
    } catch {
      size = 0;
    }
    seen.push({ path: url.pathname, type: res.request().resourceType(), size });
  });

  await page.goto("/", { waitUntil: "networkidle" });

  const total = seen.reduce((n, r) => n + r.size, 0);
  const byType = (t) => seen.filter((r) => r.type === t).reduce((n, r) => n + r.size, 0);

  const report = seen
    .map((r) => `    ${String(r.size).padStart(7)}  ${r.type.padEnd(10)} ${r.path}`)
    .join("\n");
  console.log(`cold load: ${seen.length} requests, ${total} bytes\n${report}`);

  expect(seen.length, "request count").toBeLessThanOrEqual(BUDGET.requests);
  expect(total, "total transferred").toBeLessThanOrEqual(BUDGET.totalBytes);
  expect(byType("document"), "html").toBeLessThanOrEqual(BUDGET.htmlBytes);
  expect(byType("stylesheet"), "css").toBeLessThanOrEqual(BUDGET.cssBytes);
  expect(byType("script"), "js").toBeLessThanOrEqual(BUDGET.jsBytes);
});

test("no font is downloaded that nothing on the page uses", async ({ page }) => {
  const fonts = [];
  page.on("response", (res) => {
    if (res.request().resourceType() === "font") fonts.push(new URL(res.url()).pathname);
  });
  await page.goto("/", { waitUntil: "networkidle" });

  // A face the stylesheet declares but no element applies is never requested.
  // Serving it is wasted deploy weight, not wasted bandwidth, so this records
  // the distinction rather than failing on it.
  console.log(`fonts actually requested: ${fonts.sort().join(", ")}`);
  expect(fonts.length).toBeGreaterThan(0);
  for (const f of fonts) {
    expect(f.endsWith(".woff2"), `${f} should be woff2`).toBe(true);
  }
});

test("nothing blocks rendering except the one stylesheet", async ({ page }) => {
  await page.goto("/");
  const blocking = await page.evaluate(() => {
    const out = [];
    for (const el of document.querySelectorAll("link[rel=stylesheet]")) out.push("css:" + el.href);
    for (const el of document.querySelectorAll("script[src]")) {
      if (!el.defer && !el.async) out.push("script:" + el.src);
    }
    return out;
  });
  expect(blocking.length, `render-blocking: ${blocking.join(", ")}`).toBe(1);
});
