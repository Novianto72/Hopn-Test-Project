from playwright.sync_api import sync_playwright

def test_login_page():
    with sync_playwright() as p:
        # Launch browser (set headless=False to see the browser)
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            # Navigate to the login page
            print("Navigating to login page...")
            page.goto("https://wize-invoice-dev-front.octaprimetech.com/login")
            page.pause()
            # Wait for the page to load
            page.wait_for_selector("input[type='email']", timeout=10000)
            print("Login page loaded successfully!")
            
            # Take a screenshot
            page.screenshot(path="login_page.png")
            print("Screenshot saved as 'login_page.png'")
            
            # Keep the browser open for inspection
            print("Press Enter to close the browser...")
            input()
            
        except Exception as e:
            print(f"An error occurred: {e}")
            page.screenshot(path="error.png")
            print("Screenshot of the error saved as 'error.png'")
        finally:
            # Close the browser
            browser.close()

if __name__ == "__main__":
    test_login_page()
