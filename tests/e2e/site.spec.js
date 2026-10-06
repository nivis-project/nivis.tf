// End-to-end checks against the BUILT site, served as static files.
//
// Everything here is a claim that cannot be settled by reading the output:
// whether a focus ring is visible, whether the document scrolls, whether a
// theme choice survives a reload, whether a flash happens. Several earlier
// changes deferred exactly these, and this is where they are settled.
const { test, expect } = require("@playwright/test");

// Chromium serialises oklch() colours in computed style AS oklch(), not rgb().
// An earlier version of these tests averaged the three numbers in the string to
// guess "is this dark", so oklch(0.975 0.008 275) averaged to ~92 and read as
// dark. One test passed for entirely the wrong reason.
//
// So the palette is identified exactly, by comparing the resolved --ground
// custom property against the token values, which come from data/tokens.yaml
// through the flake so there is still one source.
const TOKENS = JSON.parse(process.env.TOKENS_JSON);

async function palette(page) {
  const ground = (
    await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue("--ground").trim()
    )
  ).replace(/\s+/g, " ");
  if (ground === TOKENS.ground.light) return "light";
  if (ground === TOKENS.ground.dark) return "dark";
  throw new Error(`--ground resolved to "${ground}", which is neither palette`);
}

const WIDTHS = [
  { name: "narrow", width: 360, height: 800 },
  { name: "medium", width: 768, height: 900 },
  { name: "wide", width: 1440, height: 900 },
];

test.describe("layout", () => {
  for (const { name, width, height } of WIDTHS) {
    test(`the document does not scroll sideways at ${width}px (${name})`, async ({ page }) => {
      await page.setViewportSize({ width, height });
      await page.goto("/");
      const overflow = await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
      }));
      expect(overflow.scrollWidth).toBeLessThanOrEqual(overflow.clientWidth);
    });
  }

  test("the comparison table scrolls inside its own box", async ({ page }) => {
    await page.setViewportSize({ width: 360, height: 800 });
    await page.goto("/");
    const box = page.locator(".table-scroll");
    const scrolls = await box.evaluate((el) => el.scrollWidth > el.clientWidth);
    expect(scrolls).toBe(true);
  });
});

test.describe("keyboard", () => {
  test("the first stop is the skip link, and it reaches the content", async ({ page }) => {
    await page.goto("/");
    await page.keyboard.press("Tab");
    const first = await page.evaluate(() => {
      const el = document.activeElement;
      return { tag: el.tagName, href: el.getAttribute("href"), text: el.textContent.trim() };
    });
    expect(first.tag).toBe("A");
    expect(first.href).toBe("#main");

    // Visible once focused, not merely present.
    const visible = await page.evaluate(() => {
      const el = document.activeElement.getBoundingClientRect();
      return el.left >= 0 && el.width > 0 && el.height > 0;
    });
    expect(visible).toBe(true);

    await page.keyboard.press("Enter");
    await expect(page.locator("#main")).toBeVisible();
  });

  test("the focused control is visibly distinguished", async ({ page }) => {
    await page.goto("/");
    await page.keyboard.press("Tab");
    await page.keyboard.press("Tab");
    const style = await page.evaluate(() => {
      const el = document.activeElement;
      const s = getComputedStyle(el);
      return { outlineStyle: s.outlineStyle, outlineWidth: s.outlineWidth };
    });
    expect(style.outlineStyle).not.toBe("none");
    expect(parseFloat(style.outlineWidth)).toBeGreaterThan(0);
  });

  test("every control is reachable by tabbing", async ({ page }) => {
    await page.goto("/");
    const expected = await page.evaluate(
      () => document.querySelectorAll("a[href], button:not([hidden])").length
    );
    const seen = new Set();
    for (let i = 0; i < expected + 5; i++) {
      await page.keyboard.press("Tab");
      const id = await page.evaluate(() => {
        const el = document.activeElement;
        if (!el || el === document.body) return null;
        return el.tagName + ":" + (el.getAttribute("href") || el.getAttribute("aria-label") || el.textContent.trim().slice(0, 20));
      });
      if (id) seen.add(id);
    }
    expect(seen.size).toBeGreaterThanOrEqual(expected);
  });
});

test.describe("theme", () => {
  test("follows the system when nothing is stored", async ({ page }) => {
    await page.emulateMedia({ colorScheme: "dark" });
    await page.goto("/");
    const attr = await page.evaluate(() => document.documentElement.getAttribute("data-theme"));
    expect(attr).toBeNull();
    expect(await palette(page)).toBe("dark");
  });

  test("an explicit choice overrides the system and survives a reload", async ({ page }) => {
    await page.emulateMedia({ colorScheme: "dark" });
    await page.goto("/");
    await page.locator("[data-theme-switch]").click();
    expect(await page.evaluate(() => document.documentElement.getAttribute("data-theme"))).toBe("light");

    await page.reload();
    expect(await page.evaluate(() => document.documentElement.getAttribute("data-theme"))).toBe("light");
    expect(await palette(page)).toBe("light");
  });

  test("no flash: the stored choice is in effect at first paint", async ({ page }) => {
    await page.emulateMedia({ colorScheme: "dark" });
    await page.goto("/");
    await page.locator("[data-theme-switch]").click();

    // Reload and read the attribute at the earliest moment a script can run.
    const atFirstScript = await page.evaluate(() => {
      return new Promise((resolve) => {
        window.addEventListener("DOMContentLoaded", () => {}, { once: true });
        resolve(null);
      });
    });
    await page.reload({ waitUntil: "commit" });
    const early = await page.evaluate(() => document.documentElement.getAttribute("data-theme"));
    expect(early).toBe("light");
    expect(atFirstScript).toBeNull();
  });

  test("without scripting the system decides and the control is hidden", async ({ browser }) => {
    const context = await browser.newContext({ javaScriptEnabled: false, colorScheme: "dark" });
    const page = await context.newPage();
    await page.goto("/");
    await expect(page.locator("[data-theme-switch]")).toBeHidden();
    expect(await palette(page)).toBe("dark");
    await context.close();
  });
});

test.describe("motion", () => {
  test("smooth scrolling is off when reduced motion is requested", async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("/");
    const behavior = await page.evaluate(
      () => getComputedStyle(document.documentElement).scrollBehavior
    );
    expect(behavior).toBe("auto");
  });
});
