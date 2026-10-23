// Playwright (Node.js) with the Solvecha extension, in the Chromium that Playwright installs.
// The extension reads the reCAPTCHA image challenge, asks the API and clicks the tiles.
import { chromium } from "playwright";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { requireKey, saveKey, settings, solveDemo } from "./common.mjs";

const key = requireKey();
const extension = resolve(process.env.SOLVECHA_EXTENSION_DIR ?? "../solvecha-extension");

// Extensions need a headed browser. On a server, run this under `xvfb-run`.
const profile = await mkdtemp(join(tmpdir(), "solvecha-pw-"));
const context = await chromium.launchPersistentContext(profile, {
  headless: false,
  executablePath: process.env.CHROMIUM_PATH || undefined, // optional: a Chromium you installed yourself
  ignoreDefaultArgs: ["--enable-automation"],
  args: [
    `--disable-extensions-except=${extension}`,
    `--load-extension=${extension}`,
    "--disable-blink-features=AutomationControlled",
  ],
});

try {
  await saveKey(context, key);
  const { runs, ...rest } = settings();
  const solved = await solveDemo(context, { runs, ...rest });
  process.exitCode = solved === runs ? 0 : 1;
} finally {
  await context.close();
  await rm(profile, { recursive: true, force: true });
}
