"""Playwright (Python) without the extension: read the challenge, ask the Solvecha API, click the tiles.

Uses the "sync" mode: one request returns the answer.
"""
import base64
import os

import requests
from playwright.sync_api import sync_playwright

KEY = os.environ.get("SOLVECHA_API_KEY")
if not KEY:
    raise SystemExit("Set SOLVECHA_API_KEY (get a key at https://solvecha.com/dashboard).")

API = "https://api.solvecha.com"
DEMO = "https://www.google.com/recaptcha/api2/demo"
MAX_ROUNDS = int(os.environ.get("MAX_ROUNDS", "10"))
HEADERS = {"Authorization": f"Bearer {KEY}"}


def solve_grid(task: str, grid: str, png: bytes) -> list[bool]:
    """Returns one boolean per tile, left to right, top to bottom."""
    body = {"task": task, "grid": grid, "image_data": [base64.b64encode(png).decode()]}
    answer = requests.post(f"{API}/v1/recognition/recaptcha?sync=1", json=body, headers=HEADERS, timeout=30).json()
    for _ in range(20):
        if not isinstance(answer.get("data"), str):
            break
        # The job took longer than the sync wait: poll with the job id.
        answer = requests.get(f"{API}/v1/recognition/recaptcha", params={"id": answer["data"], "wait": 5}, headers=HEADERS, timeout=30).json()
    if not isinstance(answer.get("data"), list):
        raise RuntimeError(f"Solvecha error: {answer}")
    return answer["data"]


def run(browser) -> bool:
    page = browser.new_page()
    page.goto(DEMO)
    page.frame_locator('iframe[title="reCAPTCHA"]').locator("#recaptcha-anchor").click()
    challenge = page.frame_locator('iframe[src*="/recaptcha/api2/bframe"]')

    def token() -> str:
        return page.evaluate("document.querySelector('#g-recaptcha-response')?.value ?? ''")

    for round_no in range(1, MAX_ROUNDS + 1):
        page.wait_for_timeout(2500)
        if len(token()) > 100:
            break
        table = challenge.locator("table.rc-imageselect-table-33, table.rc-imageselect-table-44, table.rc-imageselect-table-42").first
        if not table.is_visible():
            continue
        # Wait until the pictures are loaded and the fade-in of new tiles is over.
        challenge.locator("td.rc-imageselect-tile img").last.evaluate("img => img.complete || new Promise(r => (img.onload = r))")
        page.wait_for_timeout(1500)
        tiles = challenge.locator("td.rc-imageselect-tile")
        grid = "4x4" if tiles.count() == 16 else "3x3"
        task = " ".join(challenge.locator(".rc-imageselect-instructions").inner_text().split("\n")[:2])
        answer = solve_grid(task, grid, table.screenshot())
        picked = [i + 1 for i, hit in enumerate(answer) if hit]
        print(f'round {round_no}: "{task}" {grid} -> tiles {picked or "none"}')
        for i, hit in enumerate(answer):
            if hit:
                tiles.nth(i).click()
        page.wait_for_timeout(600)
        challenge.locator("#recaptcha-verify-button").click()

    solved = len(token()) > 100
    print("solved: token received" if solved else "not solved")
    return solved


if os.environ.get("BROWSER") == "cloakbrowser":
    # CloakBrowser (see the README) returns the same Playwright objects. It starts Playwright itself.
    from cloakbrowser import launch

    browser = launch(headless=False)  # use xvfb-run on a server
    try:
        ok = run(browser)
    finally:
        browser.close()
else:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # use xvfb-run on a server
            executable_path=os.environ.get("CHROMIUM_PATH") or None,
            ignore_default_args=["--enable-automation"],
            args=["--disable-blink-features=AutomationControlled"],
        )
        try:
            ok = run(browser)
        finally:
            browser.close()

raise SystemExit(0 if ok else 1)
