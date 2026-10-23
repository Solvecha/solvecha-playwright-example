// Shared by the examples: save the key in the extension, then solve Google's reCAPTCHA demo.
export const DEMO = "https://www.google.com/recaptcha/api2/demo";

export function requireKey() {
  const key = process.env.SOLVECHA_API_KEY;
  if (!key) throw new Error("Set SOLVECHA_API_KEY (get a key at https://solvecha.com/dashboard).");
  return key;
}

// Save the key in the extension once. It stays in the profile folder.
export async function saveKey(context, key) {
  let [worker] = context.serviceWorkers();
  worker ??= await context.waitForEvent("serviceworker");
  await worker.evaluate((k) => chrome.storage.local.set({ apiKey: k }), key);
}

// Opens the demo page `runs` times, with a pause between runs (be polite to Google's page).
// The extension does the solving. Google sometimes serves a long chain of challenges, so,
// like a user, the script reloads the page for a fresh one after a while (up to `maxTries`).
export async function solveDemo(context, { runs = 1, pauseSeconds = 30, maxTries = 3, tryTimeoutMs = 90_000 } = {}) {
  let solved = 0;
  for (let run = 1; run <= runs; run++) {
    const page = await context.newPage();
    const started = Date.now();
    let ok = false;
    for (let attempt = 1; attempt <= maxTries && !ok; attempt++) {
      await page.goto(DEMO);
      try {
        // The token appears in this field when Google accepts the challenge.
        await page.waitForFunction(
          () => document.querySelector("#g-recaptcha-response")?.value.length > 100,
          null,
          { timeout: tryTimeoutMs },
        );
      } catch {
        console.log(`  run ${run}, try ${attempt}: no token after ${tryTimeoutMs / 1000} s`);
        continue;
      }
      await page.click("#recaptcha-demo-submit");
      ok = await page.waitForSelector(".recaptcha-success", { timeout: 15_000 }).then(() => true, () => false); // "Verification Success... Hooray!"
    }
    console.log(`run ${run}/${runs}: ${ok ? "solved" : "not solved"} in ${((Date.now() - started) / 1000).toFixed(1)} s`);
    if (ok) solved++;
    await page.close();
    if (run < runs) await new Promise((r) => setTimeout(r, pauseSeconds * 1000));
  }
  console.log(`${solved}/${runs} solved`);
  return solved;
}

export const settings = () => ({
  runs: Number(process.env.RUNS ?? 1),
  pauseSeconds: Number(process.env.PAUSE_SECONDS ?? 30),
  maxTries: Number(process.env.MAX_TRIES ?? 3),
  tryTimeoutMs: Number(process.env.TRY_TIMEOUT_MS ?? 90_000),
});
