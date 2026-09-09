import time
import json5
from playwright.sync_api import sync_playwright
from playwright.sync_api import Error as PlaywrightError
from helper import interact_element, has_exact_text, has_less_than_1gb, wait_and_click

# CONFIGLOADER
with open("config.json5", "r") as f:
    config = json5.load(f)

RUFNUMMER = config["RUFNUMMER"]
PASSWORT = config["PASSWORT"]
TELEGRAM_BOT_TOKEN = config["TELEGRAM_BOT_TOKEN"]

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
PLUS_ICON = 'one-icon[name="plus"]'

with sync_playwright() as p:
    try:
        browser = p.chromium.launch(headless=HEADLESS)
        p = browser.new_page()

        # LOGIN-URL ÖFFNEN
        p.goto(UEBERSICHT_URL, wait_until="domcontentloaded")

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

        print("\nAnmeldung erfolgreich.\nDatenvolumen wird überprüft...")
        time.sleep(5)
        p.reload(timeout=10000, wait_until="domcontentloaded")

        if has_less_than_1gb(p):
            print(f"Weniger als 1GB vorhanden.\nStarte Nachfüllungsprozess...")
            p.goto(DASHBOARD_URL, wait_until="domcontentloaded")

            time.sleep(2)
            if wait_and_click(p, 'one-button[slot="action"]'):
                time.sleep(2)
            else:
                raise Exception("Nachbuchen-Button konnte nicht geklickt werden.")
            time.sleep(2)

            p.goto(UEBERSICHT_URL, wait_until="domcontentloaded")
            p.reload(timeout=10000, wait_until="domcontentloaded")

            if has_less_than_1gb(p):
                print(f"Nachfüllung hat nicht funktioniert.\nWird erneut versucht...")

            print(f"Nachfüllung erfolgreich! +1GB")
        else:
            print(f"Nachfüllung nicht erforderlich")

    except PlaywrightError as e:
        if "Executable doesn't exist" in str(e):
            print(
                "Playwright konnte nicht starten.\n"
                "Hast du schon 'playwright install' in diesem Verzeichnis ausgeführt?"
            )
        else:
            print(f"Playwright Error: {e}")
