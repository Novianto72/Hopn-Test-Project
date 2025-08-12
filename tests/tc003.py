from playwright.sync_api import sync_playwright
import time


def test_signup_form():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set True for headless
        page = browser.new_page()
        page.goto("https://wizeinvoice.com/en", timeout=60000)

        # Scroll to bottom or use locator
        page.locator('input[type="email"]').scroll_into_view_if_needed()
        page.wait_for_timeout(1000)

        # Fill the email field
        test_email = "testuser@example.com"
        page.fill('input[type="email"]', test_email)
        print(f"📨 Entered email: {test_email}")

        # Click the Start Free Trial button
        page.click('button:has-text("Start Free Trial")')
        print("🚀 Clicked Start Free Trial button")
        page.wait_for_timeout(3000)

        # Check for confirmation (Success or Error)
        success_message = page.locator("text=Success").first
        error_message = page.locator("text=Invalid").first

        if success_message.is_visible():
            print("✅ Success message displayed")
        elif error_message.is_visible():
            print("❌ Error message displayed")
        else:
            print("⚠️ No visible confirmation message found")

        browser.close()


if __name__ == "__main__":
    test_signup_form()
