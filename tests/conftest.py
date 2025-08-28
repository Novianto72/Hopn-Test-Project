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
def authenticate(page: Page, credentials: Optional[Dict[str, str]] = None, test_name: str = "auth") -> bool:
    """
    Authenticate user with given credentials
    
    Args:
        page: Playwright page object
        credentials: Dictionary containing 'email' and 'password' keys
        test_name: Name of the test for screenshot naming
        
    Returns:
        bool: True if authentication was successful
    """
    # Use default credentials if none provided
    if not credentials:
        credentials = CREDENTIALS["DEFAULT"]
    
    try:
        # Navigate to login page
        page.goto(LOGIN_URL, wait_until="domcontentloaded")
        
        # Wait for login form to be visible
        page.wait_for_selector('input[name="email"]', state="visible", timeout=10000)
        
        # Fill in credentials
        page.fill('input[name="email"]', credentials["email"])
        page.fill('input[name="password"]', credentials["password"])
        
        # Click login button
        page.click('button[type="submit"]')
        
        # Wait for navigation to complete
        try:
            page.wait_for_url("**/dashboard", timeout=10000)
            return True
        except Exception as e:
            # Check for login error
            error_selector = '.MuiAlert-filledError, [data-testid="error-message"]'
            if page.is_visible(error_selector):
                error_text = page.text_content(error_selector)
                print(f"Login failed: {error_text}")
            return False
            
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        # Take screenshot on error
        take_screenshot(page, f"{test_name}_auth_error", "auth")
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
    # Get test class instance if it exists
    test_class = getattr(request, "instance", None)
    
    # Get credentials from test class or use default
    if hasattr(test_class, 'credentials'):
        credentials = test_class.credentials
    elif 'credentials' in request.fixturenames:
        # Get credentials from fixture if it's a parameter
        credentials = request.getfixturevalue('credentials')
    else:
        # Use default credentials
        credentials = None
    
    # Get test name for logging and screenshots
    test_name = request.node.name
    
    # Authenticate
    try:
        auth_result = authenticate(page, credentials, test_name=test_name)
        if not auth_result:
            pytest.fail("Failed to authenticate")
        
        # Take screenshot after successful login
        from tests.utils.screenshot_utils import take_screenshot
        take_screenshot(page, f"{test_name}_logged_in", "login")
        
        # Return the logged-in page
        yield page
        
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
            take_screenshot(page, f"{test_name}_logout_failed", test_type)
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
def home_page(page: Page, logged_in_page: Page) -> Page:
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
