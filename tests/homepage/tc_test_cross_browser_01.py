"""
Cross-browser compatibility tests for the Book a Demo form.
"""
import pytest
from playwright.sync_api import expect
from tests.homepage.page_objects.home_page import HomePage
from tests.config.test_config import TestConfig

# Test data - using field names that match the actual form
VALID_FORM_DATA = {
    'fullName': 'John Doe',
    'email': 'john.doe@example.com',
    'mobileNumber': '1234567890',
    'favoritConnectionMethod': 'Email',
    'message': 'Cross-browser test message'
}

# List of browsers to test
BROWSERS = ['chromium', 'firefox', 'webkit']

@pytest.mark.parametrize('browser_type', BROWSERS)
def test_form_submission_across_browsers(playwright, browser_type):
    """Test form submission works across different browsers."""
    # Launch the specified browser
    browser = getattr(playwright, browser_type).launch(
        headless=TestConfig.HEADLESS, 
        slow_mo=TestConfig.SLOW_MO
    )
    context = browser.new_context(viewport=TestConfig.VIEWPORT)
    page = context.new_page()
    
    try:
        # Initialize page with the current browser context
        home_page = HomePage(page)
        home_page.load()
        
        # Navigate to the form
        home_page.navigate_to_book_demo_section()
        
        # Wait for form to be visible
        form = page.locator(home_page.locators.BOOK_DEMO_FORM)
        expect(form).to_be_visible()
        
        # Fill the form using the page object method
        home_page.fill_demo_form(**{
            'full_name': VALID_FORM_DATA['fullName'],
            'email': VALID_FORM_DATA['email'],
            'mobile_number': VALID_FORM_DATA['mobileNumber'],
            'contact_method': VALID_FORM_DATA['favoritConnectionMethod'],
            'message': VALID_FORM_DATA['message']
        })
        
        # Verify form fields are filled correctly using the page object's locators
        for field, value in VALID_FORM_DATA.items():
            if field != 'favoritConnectionMethod':  # Skip select elements
                field_locator = page.locator(f'[name="{field}"]')
                expect(field_locator).to_have_value(value, timeout=5000)
        
        # Verify contact method is selected
        contact_method = page.locator('select[name="favoritConnectionMethod"]')
        expect(contact_method).to_have_value(VALID_FORM_DATA['favoritConnectionMethod'])
        
    finally:
        # Clean up
        context.close()
        browser.close()

def test_form_works_with_different_viewports(playwright):
    """Test form works with different viewport sizes."""
    # Launch browser
    browser = playwright.chromium.launch(headless=TestConfig.HEADLESS, slow_mo=TestConfig.SLOW_MO)
    
    # Test different viewport sizes
    viewports = [
        {'width': 320, 'height': 568},   # iPhone SE
        {'width': 375, 'height': 667},   # iPhone 6/7/8
        {'width': 768, 'height': 1024},  # iPad
        {'width': 1280, 'height': 720},  # HD
        {'width': 1440, 'height': 900}   # MacBook
    ]
    
    for viewport in viewports:
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        try:
            home_page = HomePage(page)
            home_page.load()
            home_page.navigate_to_book_demo_section()
            
            # Verify form is visible
            form = page.locator('form')
            expect(form).to_be_visible()
            
            # Verify all form elements are visible
            form_elements = [
                'input[name="fullName"]',
                'input[name="email"]',
                'input[name="mobileNumber"]',
                'select[name="favoritConnectionMethod"]',
                'textarea[name="message"]',
                'button[type="submit"]'
            ]
            
            for element in form_elements:
                locator = page.locator(element)
                expect(locator).to_be_visible()
                
        finally:
            context.close()
    
    browser.close()
