import os
import time
import traceback

import json5
import sys
import io
import re
import random
import curl_cffi
from playwright.sync_api import sync_playwright
from playwright.sync_api import Error as PlaywrightError

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
RUFNUMMER_INPUT = "input-5"
PASSWORT_INPUT = "input-6"
LOGIN_BUTTONCLASS = (
    "button button--solid button--medium button--color-default button--has-label"
)

# SEITE: DASHBOARD_URL
TOPUP_BUTTONCLASS = "button button--solid button--medium button--color-default button--has-label button--circle"

with sync_playwright() as p:
    try:
        browser = p.chromium.launch(headless=HEADLESS)
        page = browser.new_page()

        # LOGIN-URL ÖFFNEN
        page.goto(LOGIN_URL, wait_until="domcontentloaded")

        # RUFNUMMER EINGEBEN
        page.click(RUFNUMMER_INPUT)
        page.fill(RUFNUMMER, RUFNUMMER_INPUT)

        # PASSWORT EINGEBEN
        page.click(PASSWORT_INPUT)
        page.fill(PASSWORT, PASSWORT_INPUT)

        # BUCHUNGSÜBERSICHT ÖFFNEN
        page.goto(UEBERSICHT_URL, wait_until="domcontentloaded")
    except PlaywrightError as e:
        if "Executable doesn't exist" in str(e):
            print(
                "Playwright konnte nicht starten. Hast du schon 'playwright install' in diesem Verzeichnis ausgeführt?"
            )
        else:
            print(f"Playwright Error: {e}")
