import time
import pytest
from playwright.sync_api import expect
from pages.expense_types.expense_types_page import ExpenseTypesPage

class TestMultipleExpenseTypeCreations:
    def log_step(self, step: str):
        """Helper method to log test steps with timestamps"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"\n[{timestamp}] {step}")

    def test_multiple_expense_type_creations(self, logged_in_page):
        """Test creating multiple expense types in sequence"""
        page = logged_in_page
        expense_types_page = ExpenseTypesPage(page)
        num_creations = 3  # Number of expense types to create
        
        self.log_step("Starting multiple expense type creation test")
        expense_types_page.navigate()
        
        # Phase 1: Create all expense types first
        created_expenses = []
        for i in range(num_creations):
            expense_name = f"Multi Test {i+1} {int(time.time())}"
            created_expenses.append(expense_name)
            
            try:
                self.log_step(f"Creating expense type {i+1}: {expense_name}")
                expense_types_page.click_new_expense_type()
                time.sleep(3)
                expense_types_page.fill_expense_type_form(expense_name)
                expense_types_page.submit_form()
                
                # Wait for creation to complete
                if not expense_types_page.wait_for_loading_animation_to_disappear():
                    self.log_step("Warning: Loading animation still visible after retries")
                
                # Verify creation
                self.log_step(f"Verifying creation of: {expense_name}")
                expense_types_page.search_expense_type(expense_name)
                expense_types_page.wait_for_loading_animation_to_disappear()
                page.wait_for_selector("table[data-slot='table']", state='visible')
                
                first_cell = page.locator("table tbody tr:first-child td[data-slot='table-cell'] div.font-medium")
                first_cell.wait_for(state='visible')
                first_cell_text = first_cell.text_content()
                
                assert first_cell_text == expense_name, \
                    f"Expected '{expense_name}' but found '{first_cell_text}'"
                
                # Clear search for next iteration
                expense_types_page.clear_search()
                
            except Exception as e:
                self.log_step(f"ERROR on iteration {i+1}: {str(e)}")
                raise
        
        # Phase 2: Clean up all created expense types
        self.log_step("Starting cleanup of created expense types")
        for i, expense_name in enumerate(created_expenses, 1):
            try:
                self.log_step(f"Deleting expense type {i}: {expense_name}")
                expense_types_page.search_expense_type(expense_name)
                expense_types_page.wait_for_loading_animation_to_disappear()
                expense_types_page.delete_first_expense_type()
                
                # Wait for deletion to complete
                if not expense_types_page.wait_for_loading_animation_to_disappear():
                    self.log_step("Warning: Loading animation still visible after delete")
                
                # Clear search and wait for it to take effect
                expense_types_page.clear_search()
                expense_types_page.wait_for_loading_animation_to_disappear()
                
                # Verify deletion
                self.log_step(f"Verifying deletion of: {expense_name}")
                expense_types_page.search_expense_type(expense_name)
                expense_types_page.wait_for_loading_animation_to_disappear()
                
                # Wait for the table to update
                page.wait_for_selector("table[data-slot='table']", state='visible')
                
                # Check for either the no results message or an empty table
                no_results = page.locator("td[data-slot='table-cell']:has-text('No expense types found')")
                data_rows = page.locator("table tbody tr:not(:has-text('No expense types found'))")
                
                # Either the no results message should be visible, or there should be no data rows
                assert no_results.is_visible() or data_rows.count() == 0, \
                    f"Expected no results for '{expense_name}' after deletion"
                
                expense_types_page.clear_search()
                
            except Exception as e:
                self.log_step(f"WARNING: Failed to clean up {expense_name}: {str(e)}")
        
        self.log_step("Test completed successfully")
