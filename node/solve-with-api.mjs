// Playwright (Node.js) without the extension: read the challenge, ask the Solvecha API, click the tiles.
// Uses the "sync" mode: one request returns the answer.
import { chromium } from "playwright";

const key = process.env.SOLVECHA_API_KEY;
if (!key) throw new Error("Set SOLVECHA_API_KEY (get a key at https://solvecha.com/dashboard).");

const API = "https://api.solvecha.com";
const DEMO = "https://www.google.com/recaptcha/api2/demo";
const MAX_ROUNDS = Number(process.env.MAX_ROUNDS ?? 10);

// Returns one boolean per tile, left to right, top to bottom.
async function solveGrid(task, grid, png) {
  const headers = { Authorization: `Bearer ${key}`, "Content-Type": "application/json" };
  const body = JSON.stringify({ task, grid, image_data: [png.toString("base64")] });
  let answer = await (await fetch(`${API}/v1/recognition/recaptcha?sync=1`, { method: "POST", headers, body })).json();
  if (typeof answer.data === "string") {
    // The job took longer than the sync wait: poll with the job id.
    for (let i = 0; i < 20 && typeof answer.data === "string"; i++) {
      answer = await (await fetch(`${API}/v1/recognition/recaptcha?id=${answer.data}&wait=5`, { headers })).json();
    }
  }
  if (!Array.isArray(answer.data)) throw new Error(`Solvecha error: ${JSON.stringify(answer)}`);
  return answer.data;
}

// BROWSER=cloakbrowser starts CloakBrowser instead (see the README). Same Playwright objects.
const browser = process.env.BROWSER === "cloakbrowser"
  ? await (await import("cloakbrowser")).launch({ headless: false })
  : await chromium.launch({
      headless: false, // use xvfb-run on a server
      executablePath: process.env.CHROMIUM_PATH || undefined,
      ignoreDefaultArgs: ["--enable-automation"],
      args: ["--disable-blink-features=AutomationControlled"],
    });
try {
  const page = await browser.newPage();
  await page.goto(DEMO);
  const anchor = page.frameLocator('iframe[title="reCAPTCHA"]');
  await anchor.locator("#recaptcha-anchor").click();
  const challenge = page.frameLocator('iframe[src*="/recaptcha/api2/bframe"]');
  const token = () => page.evaluate(() => document.querySelector("#g-recaptcha-response")?.value ?? "");

  for (let round = 1; round <= MAX_ROUNDS; round++) {
    await page.waitForTimeout(2500);
    if ((await token()).length > 100) break;
    const table = challenge.locator("table.rc-imageselect-table-33, table.rc-imageselect-table-44, table.rc-imageselect-table-42");
    if (!(await table.first().isVisible().catch(() => false))) continue;
    // Wait until the pictures are loaded and the fade-in of new tiles is over.
    await challenge.locator("td.rc-imageselect-tile img").last().evaluate((img) => img.complete || new Promise((r) => (img.onload = r)));
    await page.waitForTimeout(1500);
    const tiles = challenge.locator("td.rc-imageselect-tile");
    const count = await tiles.count();
    const grid = count === 16 ? "4x4" : "3x3";
    const task = (await challenge.locator(".rc-imageselect-instructions").innerText()).split("\n").slice(0, 2).join(" ");
    const answer = await solveGrid(task, grid, await table.first().screenshot());
    console.log(`round ${round}: "${task}" ${grid} -> tiles ${answer.flatMap((hit, i) => (hit ? [i + 1] : [])).join(", ") || "none"}`);
    for (let i = 0; i < answer.length; i++) if (answer[i]) await tiles.nth(i).click();
    await page.waitForTimeout(600);
    await challenge.locator("#recaptcha-verify-button").click();
  }

  const ok = (await token()).length > 100;
  console.log(ok ? "solved: token received" : "not solved");
  process.exitCode = ok ? 0 : 1;
} finally {
  await browser.close();
}
