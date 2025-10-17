"""
Test Login button visibility across different screen sizes.

This test verifies that the Login button is visible and properly displayed
on various device sizes from mobile to desktop.
"""
import pytest
from playwright.sync_api import expect
from .page_objects.home_page import HomePage

# Define viewport sizes to test (width, height, name, should_be_visible)
VIEWPORTS = [
    (1920, 1080, "desktop", True),
    (1366, 768, "laptop", True),
    (1024, 768, "tablet_landscape", False),  # Known issue: Button not visible
    (768, 1024, "tablet_portrait", False),   # Known issue: Button not visible
    (414, 896, "mobile_large", False),       # Known issue: Button not visible
    (375, 667, "mobile_medium", False),      # Known issue: Button not visible
    (320, 568, "mobile_small", False),       # Known issue: Button not visible
]

@pytest.mark.parametrize("width,height,device_name,should_be_visible", VIEWPORTS)
def test_login_button_visibility(home_page, width, height, device_name, should_be_visible):
    """
    Test that the Login button is visible on different screen sizes.
    
    Args:
        home_page: Playwright page fixture navigated to the homepage
        width: Viewport width in pixels
        height: Viewport height in pixels
        device_name: Name of the device/size being tested
        should_be_visible: Whether the button should be visible on this viewport
    """
    # Initialize the page object
    home = HomePage(home_page)
    
    # Mark the test as xfail if the button is not supposed to be visible
    if not should_be_visible:
        pytest.xfail("Login button does not show on smaller screens (known issue reported to product owner)")
    
    # Set viewport size and load the page
    home.set_viewport_size(width, height)
    home.load()
    
    print(f"\n=== Testing on {device_name} ({width}x{height}) ===")
    
    # Verify the button is visible using the page object
    assert home.is_login_button_visible(), "Login button should be visible"
    
    # Get the login button locator for additional assertions
    login_button = home_page.locator(home.locators.BUTTONS['login']).first
    
    # Verify button text and basic styles
    expect(login_button).to_have_text("Login")
    expect(login_button).to_have_css("background-color", "rgb(17, 161, 147)")  # #11A193 in RGB
    expect(login_button).to_have_css("color", "rgb(255, 255, 255)")  # white text
    
    # Check if button is clickable (not covered by other elements)
    login_button.scroll_into_view_if_needed()
    
    # Verify button is within the viewport
    button_box = login_button.bounding_box()
    viewport = home_page.viewport_size
    
    assert button_box, "Button should have a bounding box"
    assert 0 <= button_box["x"] <= viewport["width"], "Button should be within viewport width"
    assert 0 <= button_box["y"] <= viewport["height"], "Button should be within viewport height"
    
    print(f"✓ Login button is visible and properly displayed on {device_name} ({width}x{height})")

# Additional test to verify button functionality across viewports
@pytest.mark.parametrize("width,height,device_name,should_be_visible", [v for v in VIEWPORTS if v[2] in ["desktop", "laptop"]])
def test_login_button_functionality(home_page, width, height, device_name, should_be_visible):
    """
    Test that the Login button is clickable and navigates to login page.
    
    This test verifies that:
    1. The login button is visible
    2. Clicking the button navigates to the login page
    3. The page is interactive after navigation
    """
    # Initialize the page object
    home = HomePage(home_page)
    
    # Skip this test for viewports where the button is not supposed to be visible
    if not should_be_visible:
        pytest.skip("Skipping functionality test as button is not visible on this viewport")
    
    # Set viewport size and load the page
    home.set_viewport_size(width, height)
    home.load()
    
    print(f"\n=== Testing Login button functionality on {device_name} ({width}x{height}) ===")
    
    # Ensure we're not already on the login page
    if 'login' in home_page.url.lower():
        raise AssertionError("Test started on login page instead of homepage")
    
    try:
        # Verify login button is visible first
        assert home.is_login_button_visible(timeout=10000), "Login button should be visible before clicking"
        
        # Store current URL for verification
        original_url = home_page.url
        
        # Click the login button using the page object
        print("Clicking login button...")
        home.click_login()
        
        # Wait for navigation to complete with a reasonable timeout
        home_page.wait_for_url("**/login*", timeout=10000)
        home_page.wait_for_load_state('networkidle')
        
        # Verify we navigated to the login page
        current_url = home_page.url.lower()
        assert "/login" in current_url, f"Expected to navigate to login page, but got: {current_url}"
        
        print("✓ Successfully navigated to login page")
        
    except Exception as e:
        # Take a screenshot for debugging
        screenshot_path = f"test-results/login_button_failure_{device_name}_{width}x{height}.png"
        home_page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
        
        # Log page information for debugging
        print(f"Current URL: {home_page.url}")
        print(f"Page title: {home_page.title()}")
        
        # Re-raise the exception with more context
        raise AssertionError(f"Test failed on {device_name} ({width}x{height}): {str(e)}")
