import os
import time
import traceback
from asyncio import wait_for

import json5
import sys
import io
import re
import random
import curl_cffi
from playwright.sync_api import sync_playwright
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from helper import interact_element, wait_for_element, has_exact_text

# CONFIGLOADER
with open("config.json5", "r") as f:
    config = json5.load(f)

RUFNUMMER = config["RUFNUMMER"]
PASSWORT = config["PASSWORT"]
TELEGRAM_BOT_TOKEN = config["TELEGRAM_BOT_TOKEN"]

LOGIN_URL = "https://login.alditalk-kundenbetreuung.de/signin/XUI/#login/"
UEBERSICHT_URL = "https://www.alditalk-kundenportal.de/portal/auth/buchungsuebersicht/"
DASHBOARD_URL = "https://www.alditalk-kundenportal.de/portal/auth/uebersicht/"

# BROWSER & HTML ID's / Classes
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"  # CHROME 152
HEADLESS = config["HEADLESS"]

# SEITE: LOGIN_URL
RUFNUMMER_INPUT = "#input-5"
PASSWORT_INPUT = "#input-6"
LOGIN_BUTTONCLASS = "Anmelden"

DENY_COOKIES = "uc-deny-all-button"

# SEITE: DASHBOARD_URL
TOPUP_BUTTONCLASS = "button button--solid button--medium button--color-default button--has-label button--circle"


def click_element(page, selector, timeout=5000):
    selectors = [
        selector,
        f'[data-testid="{selector}"]',
        f'text="{selector}"',
    ]

    for current_selector in selectors:
        try:
            page.locator(current_selector).click(timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            pass

    # Try semantic locators
    for locator in [
        page.get_by_role("button", name=selector),
        page.get_by_role("link", name=selector),
        page.get_by_text(selector),
    ]:
        try:
            locator.click(timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            pass

    raise PlaywrightTimeoutError(f"Fehler beim Klicken: {selector}")


with sync_playwright() as p:
    try:
        browser = p.chromium.launch(headless=HEADLESS)
        p = browser.new_page()

        # LOGIN-URL ÖFFNEN
        p.goto(LOGIN_URL, wait_until="domcontentloaded")

        # COOKIE BANNER HANDLEN
        interact_element(p, DENY_COOKIES)

        # LOGIN
        interact_element(p, RUFNUMMER_INPUT, RUFNUMMER)
        interact_element(p, PASSWORT_INPUT, PASSWORT)
        interact_element(p, LOGIN_BUTTONCLASS)

        if has_exact_text(p, "Anmeldung fehlgeschlagen"):
            print(
                f"\n"
                f"Die Anmeldung bei ALDITalk ist fehlgeschlagen.\nRufnummer: {RUFNUMMER}\nPasswort: {PASSWORT}"
                f"\nBitte überprüfe deine Anmeldedaten in der Config."
            )

        p.goto(LOGIN_URL, wait_until="domcontentloaded")

        # BUCHUNGSÜBERSICHT ÖFFNEN
        p.goto(UEBERSICHT_URL, wait_until="domcontentloaded")

    except PlaywrightError as e:
        if "Executable doesn't exist" in str(e):
            print(
                "Playwright konnte nicht starten. Hast du schon 'playwright install' in diesem Verzeichnis ausgeführt?"
            )
        else:
            print(f"Playwright Error: {e}")
