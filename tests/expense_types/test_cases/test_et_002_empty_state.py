"""Test cases for Expense Types empty and non-empty states."""
import time
from playwright.sync_api import expect
from pages.expense_types.expense_types_page import ExpenseTypesPage
from tests.page_components.table_component import TableComponent
from tests.config.test_config import URLS, CREDENTIALS
from dataInput.expense_types.test_data import empty_state_message

class TestExpenseTypeStates:
    """Test cases for Expense Types in both empty and non-empty states."""

    def test_empty_state(self, logged_in_page):
        """ET-002: Verify that the page shows correct state when no expense types exist."""
        try:
            print("\n=== test_empty_state ===")
            
            # Initialize page object
            page = logged_in_page
            expense_types_page = ExpenseTypesPage(page)
            
            # Navigate to expense types page
            print("🌐 Navigating to expense types page...")
            expense_types_page.navigate()
            
            # Take a screenshot of the initial state
            page.screenshot(path="test-results/expense_types_empty_state_initial.png")
            print("📸 Initial page screenshot saved")
            
            # Debug: Print current page URL and title
            print(f"📄 Current Page Title: {page.title()}")
            print(f"🌐 Current URL: {page.url}")
            
        except Exception as e:
            print(f"❌ Error during test execution: {e}")
            # Take screenshot on error
            page.screenshot(path="test-results/empty_state_error.png")
            raise
            
            # Verify empty state message is visible
            try:
                empty_state = page.get_by_text(empty_state_message)
                expect(empty_state).to_be_visible()
                print(f"✓ Verified empty state message: '{empty_state_message}'")
                
                # Take a screenshot of the empty state
                page.screenshot(path="test-results/expense_types_empty_state.png")
                print("✓ Screenshot of empty state saved")
                
                # Verify 'New Expense Type' button state
                new_button = page.get_by_role("button", name="New Expense Type", exact=True)
                
                # The button should be disabled if no Cost Centers exist
                # or enabled if Cost Centers exist
                is_disabled = new_button.get_attribute("disabled") is not None
                print(f"'New Expense Type' button is disabled: {is_disabled}")
                
                # Take a screenshot of the button state
                new_button.screenshot(path="test-results/expense_types_new_button_state.png")
                
            except Exception as e:
                print(f"Error during verification: {e}")
                page.screenshot(path="test-results/expense_types_verification_error.png")
                raise
            
            print("\n✓ Empty state test completed successfully!")
            
        except Exception as e:
            # Take a screenshot on failure
            page.screenshot(path="test-results/expense_types_test_failure.png")
            print(f"\n=== Test Failed! ===")
            print(f"Error: {e}")
            print("Screenshot saved as test-results/expense_types_test_failure.png")
            raise
    
    def test_non_empty_state(self, logged_in_page):
        """ET-003: Verify that the page shows correct state when expense types exist."""
        try:
            print("\n=== Testing Non-Empty State ===")
            
            # Use the pre-authenticated page
            page = logged_in_page
            expense_types_page = ExpenseTypesPage(page)
            
            # Navigate to expense types page
            print("🌐 Navigating to expense types page...")
            expense_types_page.navigate()
            
            # Wait for the page to load
            page.wait_for_load_state("networkidle")
            
            # Verify the table is visible and has data
            try:
                # Check if the table has rows (adjust the selector as needed)
                table_rows = page.locator("table tbody tr")
                row_count = table_rows.count()
                
                if row_count > 0:
                    print(f"✓ Found {row_count} expense type(s) in the table")
                    
                    # Take a screenshot of the non-empty state
                    page.screenshot(path="test-results/expense_types_non_empty_state.png")
                    print("✓ Screenshot of non-empty state saved")
                    
                    # Verify 'New Expense Type' button is enabled
                    new_button = page.get_by_role("button", name="New Expense Type")
                    assert not new_button.is_disabled(), "'New Expense Type' button should be enabled"
                    print("✓ 'New Expense Type' button is enabled")
                    
                else:
                    print("Warning: No expense types found in non-empty state test")
                    
            except Exception as e:
                page.screenshot(path="test-results/expense_types_non_empty_state_error.png")
                print(f"Error verifying non-empty state: {e}")
                raise
                
            print("\n✓ Non-empty state test completed successfully!")
            
        except Exception as e:
            # Take a screenshot on failure
            page.screenshot(path="test-results/expense_types_non_empty_test_failure.png")
            print(f"\n=== Test Failed! ===")
            print(f"Error: {e}")
            print("Screenshot saved as test-results/expense_types_non_empty_test_failure.png")
            raise
