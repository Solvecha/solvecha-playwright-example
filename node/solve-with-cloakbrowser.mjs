// The same script in CloakBrowser (https://github.com/CloakHQ/cloakbrowser), a Chromium build with a
// changed fingerprint. It returns normal Playwright objects. Solvecha is not affiliated with CloakHQ.
// The browser binary downloads on the first launch. Read its license first: https://cloakbrowser.dev
import { launchPersistentContext } from "cloakbrowser";
import { resolve } from "node:path";
import { requireKey, saveKey, settings, solveDemo } from "./common.mjs";

const key = requireKey();
const extension = resolve(process.env.SOLVECHA_EXTENSION_DIR ?? "../solvecha-extension");

const context = await launchPersistentContext({
  userDataDir: process.env.PROFILE_DIR ?? "./profile",
  headless: false, // use xvfb-run on a server
  extensionPaths: [extension],
  viewport: { width: 1000, height: 900 },
});

try {
  await saveKey(context, key);
  const { runs, ...rest } = settings();
  const solved = await solveDemo(context, { runs, ...rest });
  process.exitCode = solved === runs ? 0 : 1;
} finally {
  await context.close();
}
