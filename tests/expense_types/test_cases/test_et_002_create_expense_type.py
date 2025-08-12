import time
import pytest
from playwright.sync_api import expect
from pages.expense_types.expense_types_page import ExpenseTypesPage
from tests.page_components.table_component import TableComponent

class TestCreateExpenseType:
    def test_create_new_expense_type(self, logged_in_page):
        """Test creating a new expense type"""
        page = logged_in_page
        expense_types_page = ExpenseTypesPage(page)
        
        # Navigate to the expense types page
        expense_types_page.navigate()
        
        # Generate a unique name
        expense_name = f"Test Expense {int(time.time())}"
        
        # Initialize table component
        table = TableComponent(page)
        
        # Click the new button
        expense_types_page.click_new_expense_type()
    
        # Wait for the modal to be fully loaded
        time.sleep(3)
    
        try:
            # Fill the form - let the method handle cost center selection
            expense_types_page.fill_expense_type_form(expense_name)
    
            # Submit the form
            expense_types_page.submit_form()
    
            # Wait for the modal to be closed
            expect(page.locator('div[role="dialog"]')).to_have_count(0, timeout=10000)
    
            # Wait for any loading animations to complete
            expense_types_page.wait_for_loading_animation_to_disappear()
            
            # Debug: Print the current page content
            print("\n=== DEBUG: Current page content ===")
            print(page.content())
            
            # Debug: Check if the expense type appears in the table using a different method
            print("\n=== DEBUG: Checking if expense type appears in table ===")
            all_rows = expense_types_page.get_expense_types_list()
            print(f"Found {len(all_rows)} rows in the table")
            for i, row in enumerate(all_rows, 1):
                print(f"Row {i}: {row}")
                if row.get('name') == expense_name:
                    print(f"Found matching expense type in row {i}")
                    break
            
            # Wait for the new expense type to appear in the table
            print(f"\n=== DEBUG: Waiting for expense type '{expense_name}' to appear in table ===")
            expense_row = expense_types_page.wait_for_expense_type_in_table(expense_name)
            assert expense_row, f"Expense type '{expense_name}' not found in the table"
            
            # Verify the expense type details in the row
            print("\n=== DEBUG: Verifying expense type details ===")
            expense_data = table.get_row_data(expense_row)
            print(f"Expense data from table: {expense_data}")
            assert expense_data['name'] == expense_name, \
                f"Expected expense name '{expense_name}' not found in table"
                
            # Verify the new item is in the table by searching for it
            expense_types_page.search_expense_type(expense_name)
            # Wait for loading animation to complete
            expense_types_page.wait_for_loading_animation_to_disappear()
            
            # Verify the search results
            rows = table.get_rows()
            # Skip the header row by starting from index 1
            data_rows = [row for row in rows[1:] if row.inner_text().strip() and 'No expense types found' not in row.inner_text()]
            
            # Debug output
            print(f"\nSearch results for '{expense_name}':")
            for i, row in enumerate(rows):
                print(f"Row {i}: {row.inner_text()}")
            
            # We should have exactly one data row with our expense
            assert len(data_rows) == 1, f"Expected 1 data row after search, found {len(data_rows)}. All rows: {[row.inner_text() for row in rows]}"
            
            # Verify the expense name is in the data row
            data_row_text = data_rows[0].inner_text()
            assert expense_name in data_row_text, \
                f"Expense '{expense_name}' not found in data row. Row content: {data_row_text}"
                
            # Print success message with the created expense name
            print(f"\n✅ Successfully created expense type: {expense_name}")
            print(f"   - Cost Center: {table.get_row_data(rows[0])['cost_center'] if 'cost_center' in table.get_row_data(rows[0]) else 'N/A'}")
                
        except Exception as e:
            # Take a screenshot on failure
            page.screenshot(path=f"test_failure_{int(time.time())}.png")
            print(f"\n❌ Failed to create expense type: {expense_name}")
            raise
