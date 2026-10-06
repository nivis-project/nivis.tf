const { defineConfig } = require("@playwright/test");

// The suite runs against the BUILT site served as static files, not against
// `hugo server`: the dev server rewrites things the real deployment does not,
// and skips minification and fingerprinting.
module.exports = defineConfig({
  testDir: ".",
  fullyParallel: true,
  forbidOnly: true,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: "http://127.0.0.1:8099",
    trace: "off",
  },
  webServer: {
    command: `python3 -m http.server 8099 --bind 127.0.0.1 --directory ${process.env.SITE_DIR}`,
    url: "http://127.0.0.1:8099",
    reuseExistingServer: false,
    timeout: 30000,
  },
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
});
