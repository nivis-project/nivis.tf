// axe-core over the built page, in both palettes.
//
// axe-core is not packaged in nixpkgs, so the flake fetches it as a
// fixed-output derivation with a pinned hash, the same way nixpkgs fetches
// every other source. AXE_PATH points at it.
const fs = require("fs");
const { test, expect } = require("@playwright/test");

const axeSource = fs.readFileSync(process.env.AXE_PATH, "utf8");

async function audit(page) {
  await page.addScriptTag({ content: axeSource });
  return page.evaluate(async () => {
    const result = await window.axe.run(document, {
      resultTypes: ["violations"],
      runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"] },
    });
    return result.violations.map((v) => ({
      id: v.id,
      impact: v.impact,
      help: v.help,
      // The measured values, not just the selector. A contrast violation that
      // only names an element tells you nothing about which colours are wrong.
      nodes: v.nodes.slice(0, 6).map((n) => ({
        target: n.target.join(" "),
        why: (n.any || []).map((a) => ({ message: a.message, data: a.data })),
      })),
    }));
  });
}

for (const scheme of ["light", "dark"]) {
  test(`no accessibility violations in the ${scheme} palette`, async ({ page }) => {
    await page.emulateMedia({ colorScheme: scheme });
    await page.goto("/");
    await page.evaluate(
      (s) => document.documentElement.setAttribute("data-theme", s),
      scheme
    );
    const violations = await audit(page);
    if (violations.length) {
      console.error(JSON.stringify(violations, null, 2));
    }
    expect(violations).toEqual([]);
  });
}
