import re
import pytest
import time
from pathlib import Path
from typing import Dict, Any, Optional, Generator
from playwright.sync_api import (
    Browser, 
    BrowserContext, 
    Page, 
    BrowserType, 
    Playwright, 
    sync_playwright,
    expect
)
from tests.config.test_config import (
    TestConfig,
    URLS,
    CREDENTIALS,
    BASE_URL
)
from tests.utils.screenshot_utils import take_screenshot

# Constants
LOGIN_URL = URLS["LOGIN"]
LOGOUT_URL = f"{BASE_URL}/logout"
HOME_URL = URLS["HOME"]

# Authentication logic
def log_step(step: str):
    """Helper function to log steps with consistent formatting"""
    print(f"\n[STEP] {step}")

def authenticate(page: Page, credentials: Optional[Dict[str, str]] = None, test_name: str = "auth") -> bool:
    """
    Authenticate user with given credentials with enhanced error handling and logging.
    
    Args:
        page: Playwright page object
        credentials: Dictionary containing 'email' and 'password' keys
        test_name: Name of the test for screenshot naming
        
    Returns:
        bool: True if authentication was successful
    """
    log_step(f"Starting authentication for test: {test_name}")
    
    # Use default credentials if none provided
    if not credentials:
        log_step("Using default credentials from config")
        credentials = CREDENTIALS["DEFAULT"]
    
    log_step(f"Attempting login with email: {credentials['email']}")
    log_step(f"Starting URL: {page.url}")
    
    try:
        # Handle logout redirect if we're on the logout page
        if "/logout" in page.url.lower():
            log_step("Detected logout page. Navigating to login...")
            page.goto(LOGIN_URL, wait_until="networkidle")
        # Navigate to login page if not already there
        elif "/login" not in page.url.lower() and "/auth" not in page.url.lower():
            log_step(f"Navigating to login page: {LOGIN_URL}")
            page.goto(LOGIN_URL, wait_until="networkidle")
        
        log_step(f"Current URL: {page.url}")
        
        # Take initial screenshot
        take_screenshot(page, f"{test_name}_login_page", "auth")
        
        # Wait for login form to be visible (with multiple possible selectors)
        log_step("Waiting for login form...")
        email_selectors = [
            'input[name="email"]',
            'input[type="email"]',
            'input[data-testid="email"]',
            '#email',
            '#username',
            'input[autocomplete="username"]'
        ]
        
        email_field = None
        for selector in email_selectors:
            try:
                email_field = page.wait_for_selector(selector, state="visible", timeout=3000)
                print(f"Found email field with selector: {selector}")
                break
            except:
                continue
        
        if not email_field:
            raise Exception("Could not find email field on the page")
        
        # Find password field
        password_selectors = [
            'input[name="password"]',
            'input[type="password"]',
            'input[data-testid="password"]',
            '#password',
            'input[autocomplete="current-password"]'
        ]
        
        password_field = None
        for selector in password_selectors:
            try:
                password_field = page.wait_for_selector(selector, state="visible", timeout=2000)
                log_step(f"Found password field with selector: {selector}")
                break
            except Exception as e:
                log_step(f"Password field not found with selector {selector}: {str(e)}")
                continue
        
        if not password_field:
            raise Exception("Could not find password field on the page")
        
        # Fill in credentials
        log_step("Filling in credentials...")
        try:
            email_field.fill(credentials["email"])
            # Add a small delay to ensure the field is filled
            page.wait_for_timeout(300)
            password_field.fill(credentials["password"])
            log_step("Credentials filled")
            
            # Take screenshot after filling credentials (masking sensitive data)
            page.evaluate("""
                document.querySelectorAll('input[type="password"]').forEach(el => {
                    el.style.webkitTextSecurity = 'disc';
                });
            """)
            take_screenshot(page, f"{test_name}_credentials_filled", "auth")
            
        except Exception as e:
            log_step(f"Error filling credentials: {str(e)}")
            take_screenshot(page, f"{test_name}_fill_credentials_error", "auth")
            return False
        
        # Find and click login button
        login_button_selectors = [
            'button[type="submit"]',
            'button:has-text("Sign in")',
            'button:has-text("Log in")',
            'button:has-text("Login")',
            'button[data-testid="login-button"]',
            'form button[type="submit"]',
            'button:has-text("Continue")',
            'input[type="submit"][value*="ign" i]',
            'button:visible',
            'input[type="submit"]'
        ]
        
        login_button = None
        for selector in login_button_selectors:
            try:
                login_button = page.wait_for_selector(selector, state="visible", timeout=2000)
                button_text = login_button.inner_text().strip()
                log_step(f"Found login button with selector: {selector} (text: '{button_text}')")
                break
            except Exception as e:
                log_step(f"Login button not found with selector {selector}: {str(e)}")
                continue
        
        if not login_button:
            log_step("Could not find login button on the page")
            take_screenshot(page, f"{test_name}_login_button_not_found", "auth")
            return False
        
        log_step("Clicking login button...")
        try:
            # Scroll the button into view and click
            login_button.scroll_into_view_if_needed()
            login_button.click(delay=100)  # Add small delay to ensure click is registered
            log_step("Login button clicked")
            
            # Wait for navigation to start
            page.wait_for_load_state("networkidle", timeout=5000)
            
        except Exception as e:
            log_step(f"Error clicking login button: {str(e)}")
            take_screenshot(page, f"{test_name}_login_click_error", "auth")
            return False
        
        # Wait for navigation to complete or error to appear
        log_step("Waiting for login to complete...")
        try:
            # Wait for navigation to complete with a timeout
            page.wait_for_load_state("networkidle", timeout=15000)
            log_step(f"Navigation complete. Current URL: {page.url}")
            
            # Take screenshot after navigation
            take_screenshot(page, f"{test_name}_post_login", "auth")
            
            # Check for error messages first
            error_selectors = [
                '.MuiAlert-filledError',
                '[data-testid="error-message"]',
                '.error-message',
                '.alert-error',
                '.error',
                '.login-error',
                'div[role="alert"]',
                '.ant-message-error',
                '.error-container',
                '.login-feedback',
                'div[class*="error" i]',
                'div[class*="alert" i]',
                'div[class*="message" i]'
            ]
            
            for selector in error_selectors:
                try:
                    error_element = page.query_selector(selector)
                    if error_element and error_element.is_visible():
                        error_text = error_element.inner_text().strip()
                        if error_text:  # Only log if there's actual text
                            log_step(f"Error message found with selector '{selector}': {error_text}")
                            take_screenshot(page, f"{test_name}_login_error", "auth")
                            return False
                except Exception as e:
                    log_step(f"Error checking selector {selector}: {str(e)}")
                    continue
            
            # Check if we're on a successful page
            success_url_indicators = [
                'dashboard', 
                'home', 
                'invoices',
                'overview',
                'welcome'
            ]
            
            current_url = page.url.lower()
            if any(indicator in current_url for indicator in success_url_indicators):
                log_step(f"Login successful! Current URL: {page.url}")
                take_screenshot(page, f"{test_name}_login_success", "auth")
                return True
            else:
                # Check for any success indicators in the page content
                try:
                    page_content = page.content().lower()
                    success_indicators = [
                        'welcome',
                        'dashboard',
                        'signed in',
                        'successfully logged in',
                        'my account'
                    ]
                    
                    if any(indicator in page_content for indicator in success_indicators):
                        log_step(f"Login successful (content match). Current URL: {page.url}")
                        take_screenshot(page, f"{test_name}_login_success_content", "auth")
                        return True
                except Exception as e:
                    log_step(f"Error checking page content: {str(e)}")
                
                log_step(f"Unexpected URL after login: {page.url}")
                take_screenshot(page, f"{test_name}_unexpected_page", "auth")
                return False
            
        except Exception as nav_error:
            print(f"Navigation error: {str(nav_error)}")
            print(f"Current URL: {page.url}")
            take_screenshot(page, f"{test_name}_navigation_error", "auth")
            return False
            
    except Exception as e:
        error_msg = f"Authentication error: {str(e)}"
        log_step(error_msg)
        log_step(f"Current URL: {page.url}")
        
        try:
            # Try to get page content for debugging
            page_content = page.content()
            log_step("Page content (first 1000 chars):")
            print("-" * 80)
            print(page_content[:1000])
            print("-" * 80)
            
            # Take error screenshot
            take_screenshot(page, f"{test_name}_auth_error", "auth")
            
            # Additional debug info
            log_step("Cookies after error:")
            try:
                cookies = page.context.cookies()
                log_step(f"Found {len(cookies)} cookies")
                for cookie in cookies[:5]:  # Only show first 5 cookies
                    log_step(f"- {cookie.get('name', 'no-name')}: {cookie.get('value', 'no-value')}")
                if len(cookies) > 5:
                    log_step(f"... and {len(cookies) - 5} more cookies")
            except Exception as cookie_err:
                log_step(f"Error getting cookies: {str(cookie_err)}")
                
        except Exception as debug_err:
            log_step(f"Error during debug info collection: {str(debug_err)}")
        
        return False

# This fixture provides a browser instance
@pytest.fixture(scope="function")
def browser() -> Generator[Browser, None, None]:
    """
    Create a new browser instance for each test.
    """
    playwright = sync_playwright().start()
    
    # Launch browser with options
    browser = getattr(playwright, TestConfig.BROWSER).launch(
        headless=TestConfig.HEADLESS,
        slow_mo=TestConfig.SLOW_MO,
        args=[
            '--disable-gpu',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-setuid-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-site-isolation-trials'
        ]
    )
    
    yield browser
    
    # Cleanup
    browser.close()
    playwright.stop()

# This fixture provides a new page for each test with consistent settings
@pytest.fixture(scope="function")
def page(browser, request):
    # Ensure browser is properly initialized
    if not browser:
        raise ValueError("Browser not initialized")
        
    # Create test results directories if they don't exist
    test_results_dir = Path("test_results")
    videos_dir = test_results_dir / "videos"
    
    if not test_results_dir.exists():
        test_results_dir.mkdir()
    
    # Create a new context with consistent settings
    context = browser.new_context(
        viewport=TestConfig.VIEWPORT,
        locale='en-US',
        timezone_id='America/Los_Angeles',
        permissions=['geolocation'],
        ignore_https_errors=True,
        record_video_dir=str(videos_dir) if TestConfig.RECORD_VIDEO else None,
        record_video_size={"width": 1920, "height": 1080} if TestConfig.RECORD_VIDEO else None
    )
    
    # Create a new page
    page = context.new_page()
    
    # Set default timeout
    page.set_default_timeout(TestConfig.DEFAULT_TIMEOUT)
    
    # Set default navigation timeout
    page.set_default_navigation_timeout(TestConfig.NAVIGATION_TIMEOUT)
    
    # Set test name for better error messages and screenshots
    test_name = request.node.name
    page.test_name = test_name
    
    # Yield the page to the test
    yield page
    
    # Close the context after the test
    context.close()

# This fixture provides a logged-in page
@pytest.fixture(scope="function")
def logged_in_page(page: Page, request):
    """
    Provides a logged-in page with test-specific credentials
    
    Usage:
    1. Define credentials in your test class:
       self.credentials = {
           "email": "test+user@gmail.com",
           "password": "Test@123"
       }
    
    2. Or pass credentials directly to the test:
       def test_something(self, logged_in_page, credentials):
           # credentials will be used for login
    
    3. Use default credentials:
       def test_something(self, logged_in_page):
           # Uses DEFAULT_CREDENTIALS
    """
    print("\n" + "="*50)
    print(f"Setting up logged_in_page fixture for test: {request.node.name}")
    
    # Get test class instance if it exists
    test_class = getattr(request, "instance", None)
    print(f"Test class: {test_class.__class__.__name__ if test_class else 'None'}")
    
    # Get credentials from test class or use default
    if hasattr(test_class, 'credentials'):
        print("Using credentials from test class")
        credentials = test_class.credentials
    elif 'credentials' in request.fixturenames:
        print("Using credentials from fixture")
        credentials = request.getfixturevalue('credentials')
    else:
        print("Using default credentials from config")
        credentials = None
    
    print(f"Credentials being used: {credentials}")
    
    # Get test name for logging and screenshots
    test_name = request.node.name
    print(f"Test name: {test_name}")
    
    # Handle case where we're already on the logout page
    if "/logout" in page.url:
        print("Detected logout URL, navigating to login page...")
        page.goto(LOGIN_URL, wait_until="domcontentloaded")
        print(f"Navigated to login page: {page.url}")
    
    # Print current URL before authentication
    print(f"Current URL before auth: {page.url}")
    
    # Authenticate
    try:
        print("\nStarting authentication...")
        auth_result = authenticate(page, credentials, test_name=test_name)
        print(f"Authentication result: {auth_result}")
        
        if not auth_result:
            # Take screenshot on failure
            take_screenshot(page, f"{test_name}_auth_failed", "auth")
            print("Authentication failed. Page content:")
            print("-" * 50)
            print(page.content())
            print("-" * 50)
            
            # Try to get any error messages from the page
            error_selectors = [
                '.MuiAlert-filledError',
                '[data-testid="error-message"]',
                '.error-message',
                'div[role="alert"]',
                '.ant-message-error'
            ]
            
            for selector in error_selectors:
                try:
                    error_element = page.query_selector(selector)
                    if error_element:
                        error_text = error_element.inner_text()
                        print(f"Found error message: {error_text}")
                        break
                except:
                    continue
                    
            pytest.fail("Failed to authenticate. Check the logs and screenshots for details.")
        
        # Take screenshot after successful login
        print("Authentication successful. Taking screenshot...")
        take_screenshot(page, f"{test_name}_logged_in", "login")
        print(f"Current URL after auth: {page.url}")
        
        # Verify we're actually logged in by checking for a logged-in element
        try:
            # Adjust this selector based on your application's logged-in state indicator
            page.wait_for_selector("div[data-testid='user-menu']", timeout=5000)
            print("Verified logged-in state")
        except Exception as e:
            print(f"Warning: Could not verify logged-in state: {str(e)}")
            take_screenshot(page, f"{test_name}_login_verification_failed", "auth")
        
        # Return the logged-in page
        print("Returning logged-in page to test")
        yield page
        
    except Exception as e:
        print(f"Unexpected error in logged_in_page fixture: {str(e)}")
        take_screenshot(page, f"{test_name}_unexpected_error", "auth")
        raise
        
    except Exception as e:
        # Take screenshot on failure
        take_screenshot(page, f"{test_name}_setup_failed", "error")
        raise Exception(f"Test setup failed: {str(e)}")
    
    finally:
        # Logout after test completes
        try:
            # Wait for any ongoing operations to complete
            import time
            time.sleep(1)
            
            # Try to navigate to logout URL if it exists
            try:
                page.goto(LOGOUT_URL, timeout=10000)
                page.wait_for_load_state("networkidle")
            except Exception as e:
                print(f"Failed to navigate to logout URL: {e}")
            
            # Clear session storage and cookies
            page.evaluate('sessionStorage.clear()')
            page.context.clear_cookies()
            page.evaluate('localStorage.clear()')
            
        except Exception as e:
            print(f"Logout failed: {e}")
            # Take screenshot on logout failure
            try:
                take_screenshot(page, f"{test_name}_logout_failed", "error")
            except Exception as screenshot_error:
                print(f"Failed to take logout error screenshot: {screenshot_error}")
            take_screenshot(page, f"{test_name}_logout_failed", "error")
            # Even if logout fails, we should continue with test cleanup
            try:
                page.context.clear_cookies()
                page.evaluate('localStorage.clear()')
            except Exception as e:
                print(f"Cleanup failed: {e}")
                pass

# This fixture provides a page navigated to cost centers
@pytest.fixture(scope="function")
def cost_centers_page(logged_in_page: Page, request):
    """
    Provides a page navigated to the Cost Centers section with screenshot support
    """
    from tests.utils.screenshot_utils import take_screenshot
    
    page = logged_in_page
    test_name = request.node.name
    
    try:
        # Take screenshot before navigation
        take_screenshot(page, f"{test_name}_before_navigation", "cost_centers")
        
        # First wait for the page to be loaded at least to DOMContentLoaded
        page.wait_for_load_state("domcontentloaded")
        
        # List of possible selectors to detect page load
        possible_selectors = [
            "h1:has-text('Cost Centers')",
            "h2:has-text('Cost Centers')",
            "table",
            ".MuiDataGrid-root",  # Common Material-UI table component
            ".cost-centers-table",
            "[data-testid='cost-centers-table']",
            "[data-testid^='cost-center-']",  # Any cost center row
            "button:has-text('New Cost Center')"  # The new cost center button
        ]

        # Wait for any of the possible elements to be present with a longer timeout
        found = False
        for selector in possible_selectors:
            try:
                page.wait_for_selector(selector, state="attached", timeout=10000)
                found = True
                # Wait a bit more for any dynamic content
                import time
                time.sleep(1)  # Using time.sleep instead of wait_for_timeout
                break
            except Exception as e:
                print(f"Selector '{selector}' not found: {str(e)}")
        
        # Wait for any loading indicators to disappear
        try:
            page.wait_for_selector(".MuiCircularProgress-root", state="hidden", timeout=5000)
        except Exception:
            pass
        
        # Take screenshot after successful navigation
        take_screenshot(page, f"{test_name}_page_loaded", "cost_centers")
        
        # Additional check for the page URL
        expect(page).to_have_url(URLS["COST_CENTERS"])
        
        yield page
        
    except Exception as e:
        # Take screenshot on failure
        take_screenshot(page, f"{test_name}_navigation_failed", "cost_centers")
        raise Exception(f"Failed to navigate to Cost Centers: {str(e)}")
    
    finally:
        # Take screenshot after test completes
        try:
            take_screenshot(page, f"{test_name}_test_completed", "cost_centers")
        except Exception as e:
            print(f"Failed to take final screenshot: {e}")
        
        # Re-raise any exception that occurred in the try block
        if 'e' in locals():
            raise e

# Hook to capture test results for tracing
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture test outcome for tracing"""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)

# This fixture provides a homepage
@pytest.fixture(scope="function")
def home_page(page: Page) -> Page:
    """
    Navigate to homepage with improved error handling.
    
    Args:
        page: Playwright page object
        
    Returns:
        Page: The page navigated to the homepage
    """
    # Make sure the page is properly initialized
    if not page:
        raise ValueError("Page object is not properly initialized")
    
    try:
        # Set timeouts
        page.set_default_navigation_timeout(60000)  # 60 seconds
        page.set_default_timeout(30000)  # 30 seconds for other operations
        
        # Navigate to the homepage with a more reliable approach
        response = page.goto(
            HOME_URL,
            wait_until="domcontentloaded",
            timeout=90000  # Increased timeout to 90 seconds
        )
        
        # Check if the response is successful
        if not response or not response.ok:
            print(f"Warning: Received status {response.status if response else 'N/A'} when accessing {HOME_URL}")
        
        # Wait for either the load event or a specific element that indicates the page is ready
        try:
            # Wait for either load state or a specific element that indicates the page is ready
            page.wait_for_load_state("load", timeout=30000)  # 30s for load event
            print("Page load state 'load' reached")
        except Exception as e:
            print(f"Load state not reached, but continuing: {str(e)}")
        
        # Wait for a specific element that indicates the page is interactive
        try:
            page.wait_for_selector('body', state='visible', timeout=15000)
        except Exception as e:
            print(f"Warning: Could not verify page is interactive: {str(e)}")
        
        # Small delay to ensure all dynamic content is loaded
        import time
        time.sleep(2)  # Using time.sleep instead of wait_for_timeout
        
        return page
        
    except Exception as e:
        # Take a screenshot on error
        from tests.utils.screenshot_utils import take_screenshot
        take_screenshot(page, "homepage_navigation_error", "error")
        print(f"Error navigating to {HOME_URL}: {str(e)}")
        print(f"Page URL: {page.url}")
        print(f"Page title: {page.title()}")
        raise

# Alias for logged_in_page to maintain backward compatibility
@pytest.fixture(scope="function")
def authenticated_page(logged_in_page: Page) -> Page:
    """
    Alias for logged_in_page for backward compatibility
    """
    return logged_in_page

# Fixture for login page (unauthenticated)
@pytest.fixture(scope="function")
def login_page(page: Page) -> Page:
    """
    Provides a page navigated to the login page (unauthenticated)
    
    Args:
        page: Playwright page object
        
    Returns:
        Page: The page navigated to the login page
    """
    try:
        # Navigate to the login page
        page.goto(LOGIN_URL, wait_until="domcontentloaded")
        
        # Wait for the login form to be visible
        page.wait_for_selector('input[name="email"]', state="visible", timeout=10000)
        
        from tests.utils.screenshot_utils import take_screenshot
        take_screenshot(page, "login_page_loaded", "login")
        
        return page
        
    except Exception as e:
        # Take a screenshot on error
        take_screenshot(page, "login_page_error", "error")
        print(f"Error navigating to login page: {str(e)}")
        raise
