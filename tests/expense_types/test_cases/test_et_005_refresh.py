"""Test case for verifying the refresh functionality of Expense Types page."""
import time
from playwright.sync_api import expect
from pages.expense_types.expense_types_page import ExpenseTypesPage
from tests.page_components.table_component import TableComponent
from tests.config.test_config import URLS

class TestRefreshExpenseTypes:
    """Test cases for refreshing the Expense Types page."""
    
    def test_refresh_button(self, logged_in_page):
        """ET-005: Verify that the 'Refresh' button reloads the expense types list"""
        try:
            print("\n=== Testing Refresh Functionality ===")
            
            # Use the pre-authenticated page
            page = logged_in_page
            expense_types_page = ExpenseTypesPage(page)
            
            # Navigate to the expense types page
            print("🌐 Navigating to expense types page...")
            expense_types_page.navigate()
            
            # Wait for the page to load
            page.wait_for_selector("h1:has-text('Expense Types')", state="visible")
            
            # Initialize table component
            table = TableComponent(page)
            
            # Click the refresh button
            print("🔄 Clicking refresh button...")
            refresh_button = page.get_by_role("button", name="Refresh")
            refresh_button.click()
            
            # Wait for the page to refresh
            page.wait_for_load_state("networkidle")
            
            # Verify the page URL is still the expense types page
            expect(page).to_have_url(f"{URLS['HOME']}/expense-type")
            
            # Verify the refresh button is still visible
            expect(refresh_button).to_be_visible()
            
            # Verify the expense types table is still visible
            table_element = page.locator("table")
            expect(table_element).to_be_visible()
            
            print("✓ Refresh button test completed successfully")
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            # Take screenshot on failure
            page.screenshot(path="test-results/expense_types_refresh_failure.png")
            raise
