from playwright.sync_api import sync_playwright
import requests
import warnings
from urllib3.exceptions import NotOpenSSLWarning


def check_link_status(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        return response.status_code
    except Exception as e:
        return str(e)


def run_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://wizeinvoice.com/en", timeout=60000)

        # Select all <a> elements
        links = page.locator("a").all()

        print(f"Found {len(links)} links on the page.\n")

        for idx, link in enumerate(links):
            href = link.get_attribute("href")
            text = link.inner_text().strip()

            if not href or href.startswith("#"):
                print(f"[SKIPPED] {text or '[no text]'} → Invalid or anchor link ({href})")
                continue

            # Handle relative links
            if href.startswith("/"):
                href = f"https://wizeinvoice.com{href}"

            status = check_link_status(href)
            status_output = f"✅ OK" if status == 200 else f"❌ {status}"

            print(f"[{status_output}] {text or '[no text]'} → {href}")

        browser.close()


if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=NotOpenSSLWarning)
    run_test()
