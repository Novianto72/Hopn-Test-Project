import time
import pytest
from playwright.sync_api import expect
from pages.expense_types.expense_types_page import ExpenseTypesPage

class TestDeleteExpenseType:
    def test_delete_expense_type(self, logged_in_page):
        """Test deleting an expense type"""
        page = logged_in_page
        expense_types_page = ExpenseTypesPage(page)
        
        # First, create an expense type to delete
        expense_types_page.navigate()
        expense_name = f"Test Delete {int(time.time())}"
        
        # Click new expense type and fill the form
        expense_types_page.click_new_expense_type()
        
        # Fill the name first
        expense_types_page.fill_name_field(expense_name)
        
        # Then handle cost center selection more carefully
        # First click the dropdown to open it
        dropdown_button = expense_types_page.page.locator('button[role="combobox"]')
        dropdown_button.click()
        
        # Wait for options to be visible and select the first one
        first_option = expense_types_page.page.locator('div[role="option"]').first
        first_option.wait_for(state='visible')
        first_option.click()
        
        # Submit the form
        expense_types_page.submit_form()
        
        # Wait for success message or modal to close
        expense_types_page.page.wait_for_selector('div[role="dialog"]', state='hidden', timeout=10000)
        
        # Now delete it
        expense_types_page.search_expense_type(expense_name)
        expense_types_page.wait_for_loading_animation_to_disappear()
        expense_types_page.delete_first_expense_type()
        
        # Verify the expense type is no longer in the table
        expense_types_page.search_expense_type(expense_name)
        expense_types_page.wait_for_loading_animation_to_disappear()
        
        # Wait for the 'No expense types found' message to appear
        try:
            no_results = expense_types_page.page.get_by_text('No expense types found')
            no_results.wait_for(state='visible', timeout=5000)  # Wait up to 5 seconds
            
            # Verify no data rows are present
            rows = expense_types_page.table.get_rows()
            data_rows = [row for row in rows 
                        if row.inner_text().strip() 
                        and 'No expense types found' not in row.inner_text()
                        and 'Name' not in row.inner_text()]  # Exclude header row
            
            assert len(data_rows) == 0, f"Found {len(data_rows)} data rows when expecting 0 after deletion"
            
        except Exception as e:
            # If we get here, either the 'No results' message didn't appear or we found unexpected rows
            rows = expense_types_page.table.get_rows()
            raise AssertionError(
                f"Expense type '{expense_name}' was not properly deleted. "
                f"Found rows: {[row.inner_text() for row in rows]}"
            ) from e
