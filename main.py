import time
import urllib
import urllib.parse
import urllib.request

import json5
from playwright.sync_api import sync_playwright
from playwright.sync_api import Error as PlaywrightError
from helper import interact_element, has_exact_text, has_less_than_1gb, wait_and_click, click_while_blue

# CONFIGLOADER
with open("config.json5", "r") as f:
    config = json5.load(f)

RUFNUMMER = config["RUFNUMMER"]
PASSWORT = config["PASSWORT"]

TELEGRAM_BOT_TOKEN = config.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = config.get("TELEGRAM_CHAT_ID", "")

CHECK_INTERVAL = float(config.get("CHECK_INTERVAL", 2))  # DEFAULT 2 MINUTEN
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

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

        data = urllib.parse.urlencode(
            {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        ).encode()

        request = urllib.request.Request(url, data=data, method="POST")

        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status == 200

    except Exception as e:
        print(f"[TELEGRAM] Fehler: {e}")
        return False


def main():
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=HEADLESS)
            context = browser.new_context(user_agent=UA)
            p = context.new_page()

            # ÜBERSICHT-URL ÖFFNEN
            print("[+] Öffne ALDITalk Portal...")
            p.goto(UEBERSICHT_URL, wait_until="domcontentloaded")

            # COOKIE BANNER HANDLEN
            interact_element(p, DENY_COOKIES)
            print("[+] Cookie-Banner abgelehnt")

            # LOGIN
            print("[+] Führe Login aus...")
            interact_element(p, RUFNUMMER_INPUT, RUFNUMMER)
            interact_element(p, PASSWORT_INPUT, PASSWORT)
            interact_element(p, LOGIN_BUTTONCLASS)

            if has_exact_text(p, "Anmeldung fehlgeschlagen"):
                print(
                    f"\n"
                    f"Die Anmeldung bei ALDITalk ist fehlgeschlagen."
                    f"\nBitte überprüfe deine Anmeldedaten in der Config."
                )
                message = (
                    "❌ ALDITalk Anmeldung fehlgeschlagen.\n"
                    "Überprüfe deine Anmeldedaten in der Config."
                )
                send_telegram(message)
                raise Exception("Login fehlgeschlagen")

            print("\nAnmeldung erfolgreich.")
            send_telegram(
                "✅ ALDITalk Bot gestartet und erfolgreich angemeldet."
                "Überwachung läuft."
            )
            time.sleep(5)

            while True:
                try:
                    print("\nDatenvolumen wird überprüft...")
                    p.goto(UEBERSICHT_URL, wait_until="domcontentloaded")
                    time.sleep(4)
                    p.reload(timeout=10000, wait_until="domcontentloaded")

                    if has_less_than_1gb(p):
                        print(
                            f"Weniger als 1GB vorhanden.\nStarte Nachfüllungsprozess..."
                        )
                        send_telegram(
                            "⚠️ ALDITalk: Weniger als 1 GB Datenvolumen. Starte Nachfüllung..."
                        )

                        p.goto(DASHBOARD_URL, wait_until="domcontentloaded")
                        time.sleep(5)

                        clicks = click_while_blue(
                            p,
                            'one-button[slot="action"]',
                            max_clicks=2,
                            wait_ms=7500,
                        )

                        if clicks == 0:
                            send_telegram(
                                "❌ ALDITalk: Nachbuchen-Button war nicht blau oder konnte nicht gek lickt werden."
                            )
                            raise Exception(
                                "Nachbuchen-Button war nicht blau oder konnte nicht geklickt werden."
                            )
                        print(f"[+] Nachbuchen-Button wurde {clicks}x geklickt.")
                        time.sleep(2)

                        p.goto(UEBERSICHT_URL, wait_until="domcontentloaded")
                        p.reload(timeout=10000, wait_until="domcontentloaded")

                        if has_less_than_1gb(p):
                            print(
                                f"Nachfüllung hat nicht funktioniert.\nWird beim nächsten Intervall ({CHECK_INTERVAL} Minuten) erneut versucht..."
                            )
                            send_telegram(
                                f"❌ ALDITalk: Nachfüllung hat nicht funktioniert.\nWird beim nächsten Intervall ({CHECK_INTERVAL} Minuten) erneut versucht."
                            )
                        else:
                            print(f"Nachfüllung erfolgreich! +{clicks}GB")
                            send_telegram(
                                f"✅ ALDITalk: Nachfüllung erfolgreich! (+{clicks}GB)"
                            )
                    else:
                        print(f"Nachfüllung nicht erforderlich")

                except Exception as loop_error:
                    print(f"Fehler während der Intervall-Prüfung: {loop_error}")
                    send_telegram(
                        f"❌ ALDITalk Fehler während der Prüfung: {loop_error}"
                    )

                print(f"Warte {CHECK_INTERVAL} Minuten bis zur nächsten Überprüfung...")
                time.sleep(CHECK_INTERVAL * 60)

        except PlaywrightError as e:
            if "Executable doesn't exist" in str(e):
                print(
                    "Playwright konnte nicht starten.\n"
                    "Hast du schon 'playwright install' in diesem Verzeichnis ausgeführt?"
                )
            else:
                print(f"Playwright Error: {e}")
                send_telegram(f"❌ ALDITalk Playwright Fehler: {e}")
        except Exception as e:
            print(f"Allgemeiner Fehler: {e}")


if __name__ == "__main__":
    main()
