import time
import pytest
from playwright.sync_api import expect
from pages.expense_types.expense_types_page import ExpenseTypesPage

class TestEditExpenseType:
    def setup_method(self, method):
        """Setup method called before each test"""
        self.original_name = None
        self.new_name = None
        self.page = None

    def teardown_method(self, method):
        """Teardown method called after each test"""
        try:
            # Only proceed if we have a valid page and original_name
            if not hasattr(self, 'page') or not self.page or not self.original_name:
                return
                
            try:
                # Check if the page is still usable
                if self.page.is_closed():
                    print("Page is already closed, skipping teardown")
                    return
                    
                # Create a new page object
                expense_types_page = ExpenseTypesPage(self.page)
                
                # Use the cleanup method which is now more robust
                self.cleanup_expense_type(expense_types_page, self.original_name)
                
            except Exception as e:
                # If we get a closed page error, just log and continue
                if 'closed' in str(e).lower() or 'context' in str(e).lower():
                    print("Context already closed during teardown, skipping cleanup")
                else:
                    print(f"Error during teardown: {str(e)}")
                    # Try to take a screenshot if possible
                    try:
                        if not self.page.is_closed():
                            self.page.screenshot(path=f"teardown_error_{int(time.time())}.png")
                    except:
                        pass
        except Exception as e:
            print(f"Unexpected error in teardown: {str(e)}")

    def cleanup_expense_type(self, expense_types_page, name):
        """Helper method to clean up an expense type"""
        try:
            if not name:
                return
                
            # Clear any existing search
            expense_types_page.clear_search()
            expense_types_page.search_expense_type(name)
            expense_types_page.wait_for_loading_animation_to_disappear()
            
            # Check if the expense type exists before trying to delete
            first_row_data = expense_types_page.get_expense_types_list()
            non_empty_rows = [row for row in first_row_data if row.get('name', '').strip() and 'No expense types found' not in row.get('name', '')]
            
            if not non_empty_rows:
                print(f"Expense type '{name}' not found for cleanup")
                return
                
            # Delete the expense type
            expense_types_page.delete_first_expense_type()
            
            # Wait for the deletion to complete
            expense_types_page.wait_for_loading_animation_to_disappear()
            
            # Verify the expense type is gone
            expense_types_page.clear_search()
            expense_types_page.search_expense_type(name)
            expense_types_page.wait_for_loading_animation_to_disappear()
            
            # Check if the table shows 'No expense types found' or has no valid rows
            first_row_data = expense_types_page.get_expense_types_list()
            non_empty_rows = [row for row in first_row_data if row.get('name', '').strip() and 'No expense types found' not in row.get('name', '')]
            
            if non_empty_rows:
                print(f"Warning: Expense type '{name}' might still exist after cleanup")
        except Exception as e:
            print(f"Cleanup error for '{name}': {str(e)}")

    def test_edit_name_expense_type(self, logged_in_page):
        """Test editing only the name of an expense type"""
        self.page = logged_in_page
        expense_types_page = ExpenseTypesPage(self.page)
        self.original_name = f"Test Edit {int(time.time())}"
        self.new_name = f"Updated {self.original_name}"
        
        try:
            # Create the expense type
            expense_types_page.navigate()
            
            # Create a new expense type
            expense_types_page.click_new_expense_type()
            
            # Fill the name first
            expense_types_page.fill_name_field(self.original_name)
            
            # Handle cost center selection
            dropdown_button = expense_types_page.page.locator('button[role="combobox"]')
            dropdown_button.click()
            
            # Wait for options and select the first one
            first_option = expense_types_page.page.locator('div[role="option"]').first
            first_option.wait_for(state='visible')
            first_option.click()
            
            # Submit the form
            expense_types_page.submit_form()
            
            # Wait for the modal to close
            expense_types_page.page.wait_for_selector('div[role="dialog"]', state='hidden', timeout=10000)
            
            # Search for the expense type
            expense_types_page.search_expense_type(self.original_name)
            expense_types_page.wait_for_loading_animation_to_disappear()
            
            # Wait for the row to be visible and click the menu
            menu_button = expense_types_page.page.locator("button[aria-haspopup='menu']").nth(1)
            menu_button.wait_for(state='visible')
            menu_button.click()
            
            # Click Edit menu item
            edit_button = expense_types_page.page.get_by_role("menuitem", name="Edit")
            edit_button.wait_for(state='visible')
            edit_button.click()
            
            # Wait for the edit modal and update the name
            modal = expense_types_page.get_modal_edit_expense_type()
            name_input = modal.locator("input#name")
            name_input.wait_for(state='visible')
            name_input.fill(self.new_name)
            
            # Click the edit button
            edit_button = modal.get_by_role("button", name="Edit expense type")
            edit_button.click()
            
            # Wait for the update to complete and modal to close
            expense_types_page.page.wait_for_selector('div[role="dialog"]', state='hidden', timeout=10000)
            
            # Search for the updated name
            expense_types_page.search_expense_type(self.new_name)
            expense_types_page.page.wait_for_timeout(1000)  # Wait for search to complete
            
            # Get the first row's data
            first_row_data = expense_types_page.get_expense_types_list()
            non_empty_rows = [row for row in first_row_data if row.get('name', '').strip()]
            
            if non_empty_rows:
                actual_name = non_empty_rows[0].get('name', '')
                assert actual_name == self.new_name, f"Expected name to be '{self.new_name}', but got '{actual_name}'"
            else:
                raise AssertionError("No expense type found in the table after edit")
                
        except Exception as e:
            # Take a screenshot on failure
            expense_types_page.page.screenshot(path=f"test_edit_name_error_{int(time.time())}.png")
            raise

    def test_edit_cost_center_expense_type(self, logged_in_page):
        """Test editing only the cost center of an expense type"""
        self.page = logged_in_page
        expense_types_page = ExpenseTypesPage(self.page)
        self.original_name = f"Test Cost Center Edit {int(time.time())}"
        
        try:
            # First, create an expense type to edit
            expense_types_page.navigate()
            
            # Create a new expense type
            expense_types_page.click_new_expense_type()
            
            # Fill the name
            expense_types_page.fill_name_field(self.original_name)
            
            # Handle cost center selection
            dropdown_button = expense_types_page.page.locator('button[role="combobox"]')
            dropdown_button.click()
            
            # Select the first option
            first_option = expense_types_page.page.locator('div[role="option"]').first
            first_option.wait_for(state='visible')
            first_option.click()
            
            # Submit the form
            expense_types_page.submit_form()
            
            # Wait for the modal to close
            expense_types_page.page.wait_for_selector('div[role="dialog"]', state='hidden', timeout=10000)
            
            # Search for the expense type
            expense_types_page.search_expense_type(self.original_name)
            
            # Click the three dots menu
            menu_button = expense_types_page.page.locator("button[aria-haspopup='menu']").nth(1)
            menu_button.wait_for(state='visible')
            menu_button.click()
            
            # Click Edit menu item
            edit_button = expense_types_page.page.get_by_role("menuitem", name="Edit")
            edit_button.wait_for(state='visible')
            edit_button.click()
            
            # Wait for the edit modal
            modal = expense_types_page.get_modal_edit_expense_type()
            
            # Click the cost center dropdown
            cost_center_dropdown = modal.locator("button[role='combobox']")
            cost_center_dropdown.click()
            
            # Get all options and select the second one if available
            # Wait for dropdown options to be visible
            print("Waiting for dropdown options to be visible...")
            listbox_selector = 'div[role="listbox"]'
            options_selector = f'{listbox_selector} div[role="option"]'
            
            try:
                # Wait for at least one option to be visible
                self.page.wait_for_selector(options_selector, state='visible', timeout=5000)
                
                # Get all options
                options = self.page.locator(options_selector).all()
                print(f"Found {len(options)} options in the dropdown")
                
                if len(options) > 1:
                    # Get the second option
                    second_option = options[1]
                    
                    # Scroll into view and click
                    second_option.scroll_into_view_if_needed()
                    second_option.hover()
                    second_option.click()
                    
                    # Wait for the selection to be applied
                    self.page.wait_for_timeout(1000)

                    # Click the edit button
                    expense_types_page.submit_edit_form()
                
                    # Verify error message appears and modal stays open
                    error_message = modal.locator("div.bg-red-50")
                    expect(error_message).to_be_visible(timeout=5000)
                
                    # Click Cancel to close the modal
                    cancel_button = modal.get_by_role("button", name="Cancel")
                    cancel_button.click()
                
                    # Wait for the modal to close
                    expense_types_page.page.wait_for_selector('div[role="dialog"]', state='hidden', timeout=10000)
                else:
                    # Take a screenshot for debugging
                    self.page.screenshot(path=f"dropdown_debug_{int(time.time())}.png")
                    print("Not enough options in the dropdown")
                    
            except Exception as e:
                print(f"Error interacting with dropdown: {str(e)}")
                self.page.screenshot(path=f"dropdown_error_{int(time.time())}.png")
                raise
                
        except Exception as e:
            # Take a screenshot on failure
            expense_types_page.page.screenshot(path=f"test_edit_cost_center_error_{int(time.time())}.png")
            raise
        finally:
            # Clean up using the helper method
            self.cleanup_expense_type(expense_types_page, self.original_name)

    def test_edit_same_cost_center_expense_type(self, logged_in_page):
        """Test editing an expense type with the same cost center"""
        self.page = logged_in_page
        expense_types_page = ExpenseTypesPage(self.page)
        self.original_name = f"Test Same Cost Center Edit {int(time.time())}"
        
        try:
            # First, create an expense type to edit
            expense_types_page.navigate()
            
            # Create a new expense type
            expense_types_page.click_new_expense_type()
            
            # Fill the name
            expense_types_page.fill_name_field(self.original_name)
            
            # Handle cost center selection
            dropdown_button = expense_types_page.page.locator('button[role="combobox"]')
            dropdown_button.click()
            
            # Select the first option
            first_option = expense_types_page.page.locator('div[role="option"]').first
            first_option.wait_for(state='visible')
            first_option.click()
            
            # Submit the form
            expense_types_page.submit_form()
            
            # Wait for the modal to close
            expense_types_page.page.wait_for_selector('div[role="dialog"]', state='hidden', timeout=10000)
            
            # Search for the expense type
            expense_types_page.search_expense_type(self.original_name)
            
            # Wait for any loading animations to complete
            expense_types_page.wait_for_loading_animation_to_disappear()
            
            # Click the three dots menu
            menu_button = expense_types_page.page.locator("button[aria-haspopup='menu']").nth(1)
            menu_button.wait_for(state='visible')
            menu_button.click()
            
            # Click Edit menu item
            edit_button = expense_types_page.page.get_by_role("menuitem", name="Edit")
            edit_button.wait_for(state='visible')
            edit_button.click()
            
            # Wait for the edit modal
            modal = expense_types_page.get_modal_edit_expense_type()
            
            # Click the cost center dropdown
            expense_types_page.fill_cost_center_field()
            
            # Click the edit button
            expense_types_page.submit_edit_form()
            
            # Wait for the modal to close
            expense_types_page.wait_for_loading_animation_to_disappear()
            
            # Clear any existing search and verify the edit was successful
            
            expense_types_page.clear_search()
            expense_types_page.search_expense_type(self.original_name)
            expense_types_page.wait_for_loading_animation_to_disappear()
            
            # Verify the expense type is still present after edit
            first_row_data = expense_types_page.get_expense_types_list()
            non_empty_rows = [row for row in first_row_data if row.get('name', '').strip()]
            assert non_empty_rows, "Expense type not found after edit"
                
        except Exception as e:
            # Take a screenshot on failure
            expense_types_page.page.screenshot(path=f"test_edit_same_cost_center_error_{int(time.time())}.png")
            raise
        finally:
            # Clean up using the helper method
            self.cleanup_expense_type(expense_types_page, self.original_name)
