import re
import pytest
import time
from pathlib import Path
from playwright.sync_api import Page, expect, sync_playwright
from typing import Dict, Any, Optional
from tests.config.test_config import URLS

# Define HOME_URL from URLS
HOME_URL = URLS["HOME"]

# Import configuration from the new config module
from tests.config.test_config import (
    URLS,
    CREDENTIALS,
    TestConfig,
    get_environment_config
)

# Define URL constants from URLS
LOGIN_URL = URLS["LOGIN"]

# Authentication logic
def authenticate(page: Page, credentials: Optional[Dict[str, str]] = None, test_name: str = "auth"):
    """
    Authenticate user with given credentials
    
    Args:
        page: Playwright page object
        credentials: Dictionary containing 'email' and 'password' keys
        test_name: Name of the test for screenshot naming
    """
    from tests.utils.screenshot_utils import take_screenshot
    
    credentials = credentials or CREDENTIALS["DEFAULT"]
    
    try:
        # Navigate to login page with retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                page.goto(URLS["LOGIN"], timeout=60000)
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    # Take screenshot before raising the exception
                    take_screenshot(page, f"{test_name}_page_load_failure", "common")
                    raise
                print(f"Login page load attempt {attempt + 1} failed, retrying...")
                time.sleep(2)
        
        # Fill in login form
        page.get_by_label("Email").fill(credentials["email"])
        page.get_by_label("Password").fill(credentials["password"])
        
        # Take screenshot before login
        take_screenshot(page, f"{test_name}_before_login", "common")
        
        # Click login
        page.get_by_role("button", name="Login").click()
        
        # Wait for successful login
        try:
            page.wait_for_url(URLS["DASHBOARD"], timeout=30000)
            # Take screenshot after successful login
            take_screenshot(page, f"{test_name}_after_login", "common")
            return True
        except Exception as e:
            # Take screenshot if login fails
            take_screenshot(page, f"{test_name}_login_failed", "common")
            raise Exception(f"Failed to verify successful login: {e}")
        
    except Exception as e:
        error_msg = f"Authentication failed: {e}"
        print(error_msg)
        # Take screenshot of the error state
        take_screenshot(page, f"{test_name}_auth_error", "common")
        raise Exception(error_msg)
        raise

# This fixture provides a browser instance
@pytest.fixture(scope="function")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=TestConfig.HEADLESS,
            slow_mo=TestConfig.SLOW_MO
        )
        yield browser
        browser.close()

# This fixture provides a new page for each test with consistent settings
@pytest.fixture(scope="function")
def page(browser, request):
    context = browser.new_context(
        viewport=TestConfig.VIEWPORT,
        ignore_https_errors=True
    )
    
    # Set default timeout for all actions
    context.set_default_timeout(TestConfig.TIMEOUT)
    
    # Start tracing
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    
    page = context.new_page()
    
    # Set test-specific attributes
    page.test_name = request.node.name.replace("[", "_").replace("]", "_")
    
    yield page
    
    # Save trace on test failure
    test_outcome = request.node.rep_call.passed if hasattr(request.node, 'rep_call') else False
    if not test_outcome:
        trace_path = f"test-results/trace-{page.test_name}.zip"
        Path("test-results").mkdir(exist_ok=True)
        context.tracing.stop(path=trace_path)
    else:
        context.tracing.stop()
    
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
    from tests.utils.screenshot_utils import take_screenshot
    
    # Get test name for screenshots
    test_name = request.node.name
    test_type = "common"
    
    # Try to determine test type from the path
    if hasattr(request.node, 'module'):
        module_path = request.node.module.__file__
        if 'cost_centers' in module_path:
            test_type = "cost_centers"
        elif 'expense_types' in module_path:
            test_type = "expense_types"
    
    # Check if test class has credentials attribute
    if hasattr(request.instance, 'credentials'):
        credentials = request.instance.credentials
    # Check if credentials were passed as a fixture parameter
    elif 'credentials' in request.fixturenames:
        credentials = request.getfixturevalue('credentials')
    else:
        credentials = None
    
    # Authenticate
    try:
        auth_result = authenticate(page, credentials, test_name=test_name)
        if not auth_result:
            pytest.fail("Failed to authenticate")
        
        # Take screenshot after successful login
        take_screenshot(page, f"{test_name}_logged_in", test_type)
        
        # Return the logged-in page
        yield page
        
    except Exception as e:
        # Take screenshot on failure
        take_screenshot(page, f"{test_name}_setup_failed", test_type)
        raise
    
    finally:
        # Cleanup - take screenshot before logout
        try:
            take_screenshot(page, f"{test_name}_before_logout", test_type)
            
            # Try different ways to find and click the logout button
            logout_selectors = [
                # Try exact match first
                {'type': 'role', 'role': 'button', 'name': 'Logout', 'exact': True},
                # Try case-insensitive match
                {'type': 'role', 'role': 'button', 'name': re.compile('logout', re.IGNORECASE)},
                # Try finding by text content
                {'type': 'text', 'text': 'Logout'},
                # Try finding by text content case-insensitive
                {'type': 'text', 'text': re.compile('logout', re.IGNORECASE)},
                # Try finding in user menu dropdown
                {'type': 'dropdown', 'menu_button': '[data-testid="user-menu"]', 'item_text': 'Logout'},
                # Try finding in profile dropdown
                {'type': 'dropdown', 'menu_button': 'button[aria-haspopup="menu"]', 'item_text': 'Logout'}
            ]
            
            logged_out = False
            for selector in logout_selectors:
                try:
                    if selector['type'] == 'role':
                        button = page.get_by_role(
                            selector['role'], 
                            name=selector['name'],
                            exact=selector.get('exact', False)
                        ).first
                        if button.is_visible():
                            button.click()
                            logged_out = True
                            break
                    elif selector['type'] == 'text':
                        button = page.get_by_text(selector['text']).first
                        if button.is_visible():
                            button.click()
                            logged_out = True
                            break
                    elif selector['type'] == 'dropdown':
                        menu_button = page.locator(selector['menu_button']).first
                        if menu_button.is_visible():
                            menu_button.click()
                            # Wait for dropdown to appear
                            page.wait_for_selector('[role="menu"]', state='visible', timeout=2000)
                            # Find and click the logout item
                            logout_item = page.get_by_role('menuitem', name=re.compile(selector['item_text'], re.IGNORECASE)).first
                            if logout_item.is_visible():
                                logout_item.click()
                                logged_out = True
                                break
                except Exception as e:
                    continue
            
            if not logged_out:
                print("Warning: Could not find logout button, attempting to clear session")
                # Clear cookies and local storage as fallback
                page.context.clear_cookies()
                page.evaluate('localStorage.clear()')
                
        except Exception as e:
            print(f"Logout failed: {e}")
            take_screenshot(page, f"{test_name}_logout_failed", test_type)
            # Even if logout fails, we should continue with test cleanup
            try:
                page.context.clear_cookies()
                page.evaluate('localStorage.clear()')
            except:
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
                page.wait_for_timeout(1000)
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
        
        return page
        
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
@pytest.fixture
def home_page(page: Page):
    """
    Navigate to homepage with improved error handling.
    
    Args:
        page: Playwright page object
        
    Returns:
        Page: The page navigated to the homepage
    """
    # Set timeouts
    page.set_default_navigation_timeout(60000)  # 60 seconds
    page.set_default_timeout(30000)  # 30 seconds for other operations
    
    try:
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
        page.wait_for_timeout(2000)
        
        return page
    
    except Exception as e:
        # Take a screenshot on error
        page.screenshot(path="test-results/homepage_navigation_error.png")
        print(f"Error navigating to {HOME_URL}: {str(e)}")
        print(f"Page URL: {page.url}")
        print(f"Page title: {page.title()}")
        raise

# Alias for logged_in_page to maintain backward compatibility
@pytest.fixture
def authenticated_page(logged_in_page: Page):
    """Alias for logged_in_page to maintain backward compatibility with tests"""
    return logged_in_page

# Fixture for login page (unauthenticated)
@pytest.fixture
def login_page(page: Page):
    """Provides a page navigated to the login page (unauthenticated)"""
    page.goto(LOGIN_URL)
    return page
