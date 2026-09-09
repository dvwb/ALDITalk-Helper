import re
import time

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


def get_locators(page, selector):
    return [
        page.locator(selector),
        page.get_by_test_id(selector),
        page.get_by_role("button", name=selector),
        page.get_by_role("link", name=selector),
        page.get_by_text(selector),
    ]


def wait_for_element(page, selector, timeout=5000):
    last_error = None

    for element in get_locators(page, selector):
        try:
            element.wait_for(state="visible", timeout=timeout)
            return
        except PlaywrightError as e:
            last_error = e

    raise PlaywrightError(
        f"Sichtbares Element '{selector}' konnte nicht gefunden werden."
    ) from last_error


def interact_element(page, selector, value=None, timeout=10000):
    print(f"\n[HELPER] Selector: {selector}")

    if value is not None:
        print("[HELPER] Aktion: FILL")
        print(f"[HELPER] Wert: {value}")

        if selector.startswith(("#", ".", "[")):
            print(f"[HELPER] CSS versuchen: {selector}")
            try:
                page.locator(selector).fill(value, timeout=timeout)
                print(f"[HELPER] ERFOLG: {selector} ausgefüllt")
                return True
            except PlaywrightTimeoutError:
                print(f"[HELPER] FEHLGESCHLAGEN: {selector}")

        print(f"[HELPER] data-testid versuchen: {selector}")
        try:
            page.get_by_test_id(selector).fill(value, timeout=2000)
            print(f"[HELPER] ERFOLG: data-testid={selector}")
            return True
        except PlaywrightTimeoutError:
            print(f"[HELPER] FEHLGESCHLAGEN: data-testid={selector}")

        raise PlaywrightTimeoutError(f"Input konnte nicht gefunden werden: {selector}")

    print("[HELPER] Aktion: CLICK")

    if " " in selector and not selector.startswith(("#", ".", "[")):
        classes = selector.split()
        css_selector = ".".join(classes)
        print(f"[HELPER] Klassen erkannt, CSS: .{css_selector}")
    else:
        css_selector = selector

    print(f"[HELPER] Link versuchen: {selector}")
    try:
        page.get_by_role("link", name=selector, exact=True).click(timeout=2000)
        print(f"[HELPER] ERFOLG: Link={selector}")
        return True
    except PlaywrightTimeoutError:
        print(f"[HELPER] FEHLGESCHLAGEN: Link={selector}")

    print(f"[HELPER] data-testid versuchen: {selector}")
    try:
        page.get_by_test_id(selector).click(timeout=2000)
        print(f"[HELPER] ERFOLG: data-testid={selector}")
        return True
    except PlaywrightTimeoutError:
        print(f"[HELPER] FEHLGESCHLAGEN: data-testid={selector}")

    print(f"[HELPER] Button versuchen: {selector}")
    try:
        page.get_by_role("button").filter(has=page.locator(f".{classes[-1]}")).click(
            timeout=2000
        )
        print(f"[HELPER] ERFOLG: Button={selector}")
        return True
    except PlaywrightTimeoutError:
        print(f"[HELPER] FEHLGESCHLAGEN: Button={selector}")

    print(f"[HELPER] CSS versuchen: {css_selector}")
    try:
        page.locator(css_selector).click(timeout=2000)
        print(f"[HELPER] ERFOLG: CSS={css_selector}")
        return True
    except PlaywrightTimeoutError:
        print(f"[HELPER] FEHLGESCHLAGEN: CSS={css_selector}")

    raise PlaywrightTimeoutError(f"Element konnte nicht geklickt werden: {selector}")


def has_exact_text(page, text, timeout=2500):
    try:
        locator = page.get_by_text(text, exact=True)

        for i in range(locator.count()):
            if locator.nth(i).is_visible():
                print(f"[HELPER] Exakten Text gefunden: {text}")
                return True

        page.wait_for_timeout(timeout)

        for i in range(locator.count()):
            if locator.nth(i).is_visible():
                print(f"[HELPER] Exakten Text gefunden: {text}")
                return True

        print(f"[HELPER] Exakten Text nicht gefunden: {text}")
        return False

    except Exception as e:
        print(f"[HELPER] Grund: {e}")
        return False


def wait_and_click(page, selector, timeout=5000, retries=5):
    for attempt in range(retries):
        try:
            print(
                f"Versuche, auf {selector} zu klicken (Versuch {attempt + 1}/{retries})..."
            )
            page.wait_for_selector(selector, timeout=timeout)
            page.click(selector)
            return True
        except TimeoutError:
            print(f"{selector} nicht gefunden. Neuer Versuch...")
            time.sleep(1)
    print(f"Konnte {selector} nicht klicken.")
    return False


def has_less_than_1gb(page, timeout=2500):
    try:
        locator = (
            page.locator('one-cluster[slot="help-text"]')
            .filter(
                has_text=re.compile(r"\d[\d.,]*\s*(MB|GB)\s+von.*Inland", re.IGNORECASE)
            )
            .first
        )

        locator.wait_for(state="visible", timeout=timeout)

        text = locator.inner_text().strip()
        print(f"[HELPER] Datenvolumen: {text}")

        match = re.search(r"([\d.,]+)\s*(MB|GB)", text, re.IGNORECASE)

        if not match:
            print("[HELPER] Kein Datenvolumen gefunden")
            return False

        value = float(match.group(1).replace(".", "").replace(",", "."))

        unit = match.group(2).upper()

        if unit == "GB":
            value_mb = value * 1024
        else:
            value_mb = value

        print(f"[HELPER] Verbleibend: {value_mb:.2f} MB")

        return value_mb < 1024

    except Exception as e:
        print(f"[HELPER] Grund: {e}")
        return False
