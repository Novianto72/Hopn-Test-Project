"""Step definitions for expense types feature."""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from playwright.sync_api import Page, expect
import os
import sys
import time

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import page objects
from pages.expense_types.expense_types_page import ExpenseTypesPage

# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the path to the features directory - use the current directory structure
features_dir = os.path.join(os.path.dirname(current_dir), "features")

# Load the feature file
scenarios(os.path.join(features_dir, "expense_types", "expense_types_page.feature"))

class _TestContext:
    def __init__(self):
        self.page = None
        self.expense_types_page = None

@pytest.fixture
def context(logged_in_page):
    """Create a context to share state between steps."""
    ctx = _TestContext()
    ctx.page = logged_in_page
    return ctx

@given("I am logged into the application")
def logged_in(context):
    """User is logged into the application."""
    # The logged_in_page fixture should handle authentication
    context.page.wait_for_load_state('networkidle')
    print("Current URL:", context.page.url)
    print("Page title:", context.page.title())
    context.page.screenshot(path='after_login.png')
    print("Screenshot saved as after_login.png")

@when("I navigate to the expense types page")
def navigate_to_expense_types(context):
    """Navigate to the expense types page."""
    # Create page object and navigate
    context.expense_types_page = ExpenseTypesPage(context.page)
    context.expense_types_page.navigate()
    
    # Wait for navigation to complete
    context.page.wait_for_load_state('networkidle')
    
    # Debug: Print page content (commented out to reduce verbosity)
    # print("\nPage content after navigation:")
    # print("-" * 50)
    # print(context.page.content())
    # print("-" * 50)
    
    # Take a screenshot for debugging
    context.page.screenshot(path='after_navigation.png')
    print("Screenshot saved as after_navigation.png")

@then('I should see the page title "Invoice AI"')
@then(parsers.parse('I should see the page title "{title}"'))
def verify_page_title(context, title):
    """Verify the page title."""
    # Wait for the page to be fully loaded
    context.page.wait_for_load_state('networkidle')
    actual_title = context.page.title()
    print(f"Actual page title: '{actual_title}'")
    print(f"Expected to contain: '{title}'")
    assert title in actual_title

@then('I should see the main heading "Expense Types"')
@then(parsers.parse('I should see the main heading "{heading}"'))
def verify_heading(context, heading):
    """Verify the main heading."""
    # Try to find any heading that contains the expected text
    heading_locator = f"//h1[contains(., '{heading}')] | //h2[contains(., '{heading}')] | //h3[contains(., '{heading}')]"
    try:
        context.page.wait_for_selector(heading_locator, state='visible', timeout=10000)
        print(f"Found heading: {heading}")
    except Exception as e:
        # Print all headings for debugging
        print("\nAvailable headings on page:")
        all_headings = context.page.locator('h1, h2, h3, h4, h5, h6').all()
        for i, h in enumerate(all_headings, 1):
            print(f"{i}. {h.inner_text()}")
        raise AssertionError(f"Could not find heading: {heading}") from e

@then('I should see the "New Expense Type" button')
@then(parsers.parse('I should see the "{button_text}" button'))
def verify_button(context, button_text):
    """Verify a button with specific text is visible."""
    # Try different ways to find the button
    selectors = [
        f"button:has-text('{button_text}')",
        f"a:has-text('{button_text}')",
        f"//button[contains(., '{button_text}')]",
        f"//a[contains(., '{button_text}')]"
    ]
    
    for selector in selectors:
        elements = context.page.locator(selector).all()
        if elements and elements[0].is_visible():
            print(f"Found button with text: '{button_text}' using selector: {selector}")
            return
    
    # If we get here, no button was found
    print(f"\nAvailable buttons on page:")
    buttons = context.page.locator('button, a.button, [role="button"]').all()
    for i, btn in enumerate(buttons, 1):
        print(f"{i}. {btn.inner_text().strip() or '<no text>'}")
    
    raise AssertionError(f"Could not find button with text: '{button_text}'")

@then("I should see the search input field")
def verify_search_input(context):
    """Verify the search input field is visible."""
    # Try different possible selectors for the search input
    selectors = [
        'input[placeholder="Search expense types..."]',  # Exact placeholder match
        'input[placeholder*="Search"]',  # Contains "Search"
        'input[type="search"]',          # Input of type search
        '[data-testid*="search"]',       # Common test ID pattern
        '.search-input',                 # Common class name
        'input.search'                   # Input with search class
    ]
    
    for selector in selectors:
        elements = context.page.locator(selector).all()
        if elements and elements[0].is_visible():
            print(f"Found search input with selector: {selector}")
            return
    
    # If we get here, no search input was found
    print("\nAvailable input fields on page:")
    inputs = context.page.locator('input, [role="search"]').all()
    for i, input_elem in enumerate(inputs, 1):
        placeholder = input_elem.get_attribute('placeholder') or 'No placeholder'
        input_type = input_elem.get_attribute('type') or 'text'
        classes = input_elem.get_attribute('class') or ''
        print(f"{i}. type='{input_type}', placeholder='{placeholder}', classes='{classes}'")
    
    raise AssertionError("Could not find search input field with any known selector")

@then("I should see the expense types page title")
def verify_page_title(expense_types_page: ExpenseTypesPage):
    """Verify the page title is correct."""
    assert "Expense Types" in expense_types_page.page.title()

@then("I should see the expense types heading")
def verify_page_heading(expense_types_page: ExpenseTypesPage):
    """Verify the page heading is correct."""
    assert expense_types_page.get_heading_text() == "Expense Types"

@then("I should see the new expense type button")
def verify_new_button(expense_types_page: ExpenseTypesPage):
    """Verify the new expense type button is visible."""
    assert expense_types_page.is_new_button_visible()
