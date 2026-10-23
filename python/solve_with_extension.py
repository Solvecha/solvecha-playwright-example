"""Playwright (Python) with the Solvecha extension, in the Chromium that Playwright installs.

The extension reads the reCAPTCHA image challenge, asks the API and clicks the tiles.
"""
import os
import shutil
import tempfile
from pathlib import Path

from common import require_key, save_key, solve_demo
from playwright.sync_api import sync_playwright

key = require_key()
extension = Path(os.environ.get("SOLVECHA_EXTENSION_DIR", "../solvecha-extension")).resolve()
profile = tempfile.mkdtemp(prefix="solvecha-pw-")

with sync_playwright() as p:
    # Extensions need a headed browser. On a server, run this under `xvfb-run`.
    context = p.chromium.launch_persistent_context(
        profile,
        headless=False,
        executable_path=os.environ.get("CHROMIUM_PATH") or None,  # optional: a Chromium you installed yourself
        ignore_default_args=["--enable-automation"],
        args=[
            f"--disable-extensions-except={extension}",
            f"--load-extension={extension}",
            "--disable-blink-features=AutomationControlled",
        ],
    )
    try:
        save_key(context, key)
        ok = solve_demo(context)
    finally:
        context.close()
        shutil.rmtree(profile, ignore_errors=True)

raise SystemExit(0 if ok else 1)
