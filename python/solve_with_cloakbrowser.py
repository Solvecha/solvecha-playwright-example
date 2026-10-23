"""The same script in CloakBrowser (https://github.com/CloakHQ/cloakbrowser), a Chromium build with a
changed fingerprint. It returns normal Playwright objects. Solvecha is not affiliated with CloakHQ.
The browser binary downloads on the first launch. Read its license first: https://cloakbrowser.dev
"""
import os
from pathlib import Path

from cloakbrowser import launch_persistent_context
from common import require_key, save_key, solve_demo

key = require_key()
extension = str(Path(os.environ.get("SOLVECHA_EXTENSION_DIR", "../solvecha-extension")).resolve())

context = launch_persistent_context(
    os.environ.get("PROFILE_DIR", "./profile"),
    headless=False,  # use xvfb-run on a server
    extension_paths=[extension],
    viewport={"width": 1000, "height": 900},
)
try:
    save_key(context, key)
    ok = solve_demo(context)
finally:
    context.close()

raise SystemExit(0 if ok else 1)
