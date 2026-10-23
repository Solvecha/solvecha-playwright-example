"""Shared by the examples: save the key in the extension, then solve Google's reCAPTCHA demo."""
import os
import time

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

DEMO = "https://www.google.com/recaptcha/api2/demo"


def require_key() -> str:
    key = os.environ.get("SOLVECHA_API_KEY")
    if not key:
        raise SystemExit("Set SOLVECHA_API_KEY (get a key at https://solvecha.com/dashboard).")
    return key


def save_key(context, key: str) -> None:
    """Save the key in the extension once. It stays in the profile folder."""
    worker = context.service_workers[0] if context.service_workers else context.wait_for_event("serviceworker")
    worker.evaluate("key => chrome.storage.local.set({ apiKey: key })", key)


def solve_demo(context) -> bool:
    """Opens the demo page RUNS times, with a pause between runs (be polite to Google's page).

    The extension does the solving. Google sometimes serves a long chain of challenges, so, like a
    user, the script reloads the page for a fresh one after a while (up to MAX_TRIES).
    Returns True when every run got a token that Google's demo form accepted.
    """
    runs = int(os.environ.get("RUNS", "1"))
    pause = int(os.environ.get("PAUSE_SECONDS", "30"))
    max_tries = int(os.environ.get("MAX_TRIES", "3"))
    try_timeout_ms = int(os.environ.get("TRY_TIMEOUT_MS", "90000"))

    solved = 0
    for run in range(1, runs + 1):
        page = context.new_page()
        started = time.time()
        ok = False
        for attempt in range(1, max_tries + 1):
            page.goto(DEMO)
            try:
                # The token appears in this field when Google accepts the challenge.
                page.wait_for_function(
                    "document.querySelector('#g-recaptcha-response')?.value.length > 100",
                    timeout=try_timeout_ms,
                )
            except PlaywrightTimeoutError:
                print(f"  run {run}, try {attempt}: no token after {try_timeout_ms // 1000} s")
                continue
            page.click("#recaptcha-demo-submit")
            try:
                page.wait_for_selector(".recaptcha-success", timeout=15_000)  # "Verification Success... Hooray!"
                ok = True
            except PlaywrightTimeoutError:
                ok = False
            if ok:
                break
        print(f"run {run}/{runs}: {'solved' if ok else 'not solved'} in {time.time() - started:.1f} s")
        solved += ok
        page.close()
        if run < runs:
            time.sleep(pause)
    print(f"{solved}/{runs} solved")
    return solved == runs
