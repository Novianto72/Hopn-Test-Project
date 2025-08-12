from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


def test_tc005_user_journey():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, devtools=True)  # Set to True for headless mode
        page = browser.new_page()
        page.goto("https://wizeinvoice.com/en", timeout=60000)

        print("🔍 Verifying landing page as a new user...")

        # Check Headline (h1)
        try:
            headline = page.locator("h1").first
            headline_text = headline.inner_text().strip()
            print(f"✅ Headline found: {headline_text}")
        except Exception as e:
            print(f"❌ Could not find or read headline: {e}")

        # Check Subheadline (first <p> after h1)
        try:
            subtext = page.locator("h1 + p").first
            sub_text_val = subtext.inner_text().strip()
            print(f"✅ Subheadline found: {sub_text_val}")
        except Exception as e:
            print(f"❌ Could not find or read subheadline: {e}")

        # Check CTA Button (Start Free Trial)
        try:
            cta = page.locator("text=Start Free Trial").first
            if cta.is_visible():
                print("✅ CTA 'Start Free Trial' is visible")
                cta.scroll_into_view_if_needed()
                cta.click()
                print("🚀 Clicked CTA button")
            else:
                print("❌ CTA button is not visible")
        except PlaywrightTimeoutError:
            print("❌ Timeout while finding CTA button")
        except Exception as e:
            print(f"❌ Error interacting with CTA button: {e}")

        # Optional: Check if "How it Works" section exists
        try:
            # how_it_works = page.locator("#how-it-works")
            how_it_works = page.locator("section#how-it-works")

            if how_it_works.bounding_box():
                print("✅ 'How it Works' section is present after CTA")
            else:
                print("⚠️ Section '#how-it-works' not in view")
        except Exception as e:
            print(f"❌ Error checking 'How it Works' section: {e}")

        # Save screenshot for review
        try:
            page.screenshot(path="tc005_landing_page.png", full_page=True)
            print("📸 Screenshot saved as tc005_landing_page.png")
        except Exception as e:
            print(f"⚠️ Could not take screenshot: {e}")

        browser.close()


if __name__ == "__main__":
    test_tc005_user_journey()
