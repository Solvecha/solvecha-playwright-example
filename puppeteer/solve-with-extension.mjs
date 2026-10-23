// Puppeteer with the Solvecha extension. Needs a headed browser: use xvfb-run on a server.
import puppeteer from "puppeteer";
import { resolve } from "node:path";

const key = process.env.SOLVECHA_API_KEY;
if (!key) throw new Error("Set SOLVECHA_API_KEY (get a key at https://solvecha.com/dashboard).");
const ext = resolve(process.env.SOLVECHA_EXTENSION_DIR ?? "../solvecha-extension");

const browser = await puppeteer.launch({
  headless: false,
  executablePath: process.env.CHROMIUM_PATH || undefined,
  ignoreDefaultArgs: ["--enable-automation"],
  args: [`--disable-extensions-except=${ext}`, `--load-extension=${ext}`, "--disable-blink-features=AutomationControlled", ...(process.env.NO_SANDBOX ? ["--no-sandbox"] : [])], // NO_SANDBOX=1 inside containers
});
try {
  // Save the key once on the settings page of the extension.
  const worker = await browser.waitForTarget((t) => t.type() === "service_worker");
  const id = new URL(worker.url()).host;
  const settings = await browser.newPage();
  await settings.goto(`chrome-extension://${id}/options.html`);
  await settings.type("#key", key);
  await settings.click("#save-key");
  await settings.close();

  const page = await browser.newPage();
  await page.goto("https://www.google.com/recaptcha/api2/demo");
  await page.waitForFunction(() => document.querySelector("#g-recaptcha-response")?.value.length > 100, { timeout: Number(process.env.TIMEOUT_MS ?? 120_000) });
  console.log("solved: token received");
} finally {
  await browser.close();
}
