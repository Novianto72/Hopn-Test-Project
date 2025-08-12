import re
from playwright.sync_api import Playwright, sync_playwright, expect
import time


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://wize-invoice-dev-front.octaprimetech.com/login")
    page.get_by_role("textbox", name="Email").click()
    page.get_by_role("textbox", name="Email").fill("noviantotito72+test12@gmail.com")
    # Note: Password should be provided via environment variable in production
    password = os.getenv('TEST_PASSWORD', 'your_test_password_here')
    page.get_by_role("textbox", name="Password").click()
    page.get_by_role("textbox", name="Password").fill(password)
    page.get_by_role("button", name="Login").click()
    page.get_by_role("link", name="Cost Centers").click()
    time.sleep(5)
    page.get_by_role("button", name="New Cost Center").click()
    page.get_by_role("textbox", name="Name *").click()
    page.get_by_role("textbox", name="Name *").fill("test play")
    page.get_by_role("button", name="Add cost center").click()
    time.sleep(5)

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
