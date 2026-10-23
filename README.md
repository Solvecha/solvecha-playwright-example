<p align="center">
  <a href="https://solvecha.com"><img src="https://solvecha.com/site/static/apple-touch-icon.png" width="64" height="64" alt="Solvecha"></a>
</p>

<h1 align="center">Solvecha + Playwright example</h1>

<p align="center">
  Solve reCAPTCHA v2 image challenges in Playwright (Node.js and Python) with the
  <a href="https://github.com/Solvecha/solvecha-extension">Solvecha browser extension</a>,
  or with the Solvecha API. Puppeteer and Selenium variants included.
</p>

<p align="center">
  <a href="https://github.com/Solvecha/solvecha-playwright-example/actions/workflows/ci.yml"><img src="https://github.com/Solvecha/solvecha-playwright-example/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT license"></a>
  <a href="https://playwright.dev"><img src="https://img.shields.io/badge/Playwright-Node.js%20%7C%20Python-2EAD33.svg" alt="Playwright"></a>
  <a href="https://solvecha.com"><img src="https://img.shields.io/badge/Solvecha-free%20tier%20100%2Fday-5b5bd6.svg" alt="Solvecha free tier"></a>
</p>

---

Two ways to get through a reCAPTCHA v2 image challenge. Both use your Solvecha API key from the environment variable `SOLVECHA_API_KEY`. **Never commit a key.**

| | Extension mode | API mode |
|---|---|---|
| What solves | The extension reads the challenge, asks the API and clicks the tiles | Your script screenshots the grid, asks the API and clicks the tiles |
| Your code | Open the page, wait for the token | About 40 lines of glue code |
| Files | `node/solve-with-extension.mjs`, `python/solve_with_extension.py` | `node/solve-with-api.mjs`, `python/solve_with_api.py` |

The test target is Google's public demo page, `https://www.google.com/recaptcha/api2/demo`. It exists for this. Run the examples a few times, not in a loop, and keep the pauses.

## Before you start

1. Create a free account on [solvecha.com](https://solvecha.com/register) and copy your key from the [dashboard](https://solvecha.com/dashboard). The free tier has 100 successful solves per day.
2. `export SOLVECHA_API_KEY=slv_...`
3. Get the extension (extension mode only):

   ```bash
   ./scripts/get-extension.sh   # downloads releases/latest/download/solvecha-chrome.zip into ./solvecha-extension
   ```

Extensions need a headed browser. On a server without a screen, put `xvfb-run -a` in front of the command.

## Playwright, Node.js

```bash
cd node
npm install
npx playwright install chromium

xvfb-run -a npm run extension    # extension mode
xvfb-run -a npm run api          # API mode
```

The core of extension mode:

```js
const context = await chromium.launchPersistentContext(profile, {
  headless: false,
  ignoreDefaultArgs: ["--enable-automation"],
  args: [`--disable-extensions-except=${extension}`, `--load-extension=${extension}`],
});

// Save the key once. It stays in the profile folder.
let [worker] = context.serviceWorkers();
worker ??= await context.waitForEvent("serviceworker");
await worker.evaluate((k) => chrome.storage.local.set({ apiKey: k }), process.env.SOLVECHA_API_KEY);

const page = await context.newPage();
await page.goto("https://www.google.com/recaptcha/api2/demo");
// The extension solves the challenge. Wait for the token:
await page.waitForFunction(() => document.querySelector("#g-recaptcha-response")?.value.length > 100);
```

## Playwright, Python

```bash
cd python
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

xvfb-run -a python solve_with_extension.py
xvfb-run -a python solve_with_api.py
```

## Settings

| Variable | Default | Meaning |
|---|---|---|
| `SOLVECHA_API_KEY` | none | Your key. Required. |
| `SOLVECHA_EXTENSION_DIR` | `../solvecha-extension` | The unzipped extension (extension mode). |
| `RUNS` | `1` | How many times the demo is solved. |
| `PAUSE_SECONDS` | `30` | Pause between runs. Keep it polite. |
| `MAX_TRIES` | `3` | Fresh challenges per run: the script reloads the page when no token arrives. |
| `TRY_TIMEOUT_MS` | `90000` | How long one try may take. |
| `CHROMIUM_PATH` | Playwright's Chromium | Use a Chromium you installed yourself. Google Chrome 137 and newer ignores `--load-extension`. |

## Fewer challenges with CloakBrowser (optional)

Google decides how hard the challenge is. On a data-center IP it can serve long chains of 4x4 challenges. [CloakBrowser](https://github.com/CloakHQ/cloakbrowser) is a Chromium build with a changed fingerprint. It returns normal Playwright objects. Solvecha is not affiliated with CloakHQ. Read its [license](https://cloakbrowser.dev) before you use it.

```bash
cd node && xvfb-run -a npm run cloakbrowser      # Node.js
cd python && xvfb-run -a python solve_with_cloakbrowser.py
BROWSER=cloakbrowser xvfb-run -a npm run api     # API mode in CloakBrowser
```

More: [Using Solvecha with CloakBrowser](https://solvecha.com/docs/cloakbrowser).

## Puppeteer and Selenium

Same idea, shorter files. The extension loads with `--load-extension`, the key is saved on the extension's settings page, then the script waits for the token.

```bash
cd puppeteer && npm install && xvfb-run -a npm start
cd selenium && pip install -r requirements.txt && xvfb-run -a python solve_with_extension.py
```

Inside a container, add `NO_SANDBOX=1`.

## Test results

Run on 23 October 2026 from a data-center IP (Linux server, Chrome for Testing 153, extension 0.1.2, Solvecha free tier). Each run is one session on Google's demo page, 30 seconds apart.

| Script | Result |
|---|---|
| Playwright Node.js, extension mode | 3 of 3 sessions solved |
| Playwright Python, extension mode | 3 of 3 sessions solved (one needed a reload for a fresh challenge) |
| Playwright Node.js and Python, CloakBrowser, extension mode | 3 of 3 sessions solved each |
| Playwright Node.js and Python, API mode (CloakBrowser) | 1 of 1 each, token after 3 rounds |
| Puppeteer, Selenium (extension mode) | 1 of 1 each, token received |

Google's difficulty changes with the IP and the browser. In an earlier test on the same IP, plain Playwright Chromium got no token in three tries, and CloakBrowser got one right after. The CI of this repository only checks syntax, because the examples need a key and a real browser.

## Links

[Website](https://solvecha.com) · [Docs](https://solvecha.com/docs/browser-extension) · [Extension releases](https://github.com/Solvecha/solvecha-extension/releases) · [Agent skills](https://github.com/Solvecha/solvecha-skills) · [Migrate from NopeCHA](https://github.com/Solvecha/nopecha-to-solvecha)

MIT licensed. Solvecha is not affiliated with Google, Playwright, CloakHQ, NopeCHA or CapSolver.
