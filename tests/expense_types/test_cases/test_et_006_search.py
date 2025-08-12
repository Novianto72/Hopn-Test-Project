import time
import pytest
import random
import string
from playwright.sync_api import expect
from pages.expense_types.expense_types_page import ExpenseTypesPage

class TestExpenseTypeSearch:
    @pytest.fixture(autouse=True)
    def setup(self, logged_in_page):
        """Setup test data before each test"""
        self.page = logged_in_page
        self.expense_types_page = ExpenseTypesPage(self.page)
        
        # Generate a more unique test ID to avoid conflicts
        self.unique_id = f"{int(time.time())}{''.join(random.choices(string.digits, k=3))}"
        self.expense_name = f"SearchTest{self.unique_id}"  # No spaces for more reliable searching
        self.partial_name = self.expense_name[:8]  # First 8 characters for partial search
        
        # Navigate to expense types page and wait for it to load
        self.expense_types_page.navigate()
        self.expense_types_page.wait_for_loading_animation_to_disappear()
        
        # Create test expense type with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"\nCreating test expense type (attempt {attempt + 1}/{max_retries})...")
                self._create_test_expense_type()
                break  # If successful, exit the retry loop
            except Exception as e:
                if attempt == max_retries - 1:  # Last attempt
                    print(f"Failed to create test expense type after {max_retries} attempts")
                    raise
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                self.page.reload()
                self.page.wait_for_load_state("networkidle")
    
    def _create_test_expense_type(self):
        """Helper method to create a test expense type with proper waiting"""
        # Click new expense type button and wait for the modal
        self.expense_types_page.click_new_expense_type()
        
        # Fill and submit the form with retry logic
        self.expense_types_page.fill_expense_type_form(self.expense_name)
        
        # Submit the form and wait for success
        if not self.expense_types_page.submit_form():
            raise Exception("Failed to submit expense type form")
        
        # Wait for the expense type to appear in the table
        print(f"Waiting for expense type '{self.expense_name}' to appear in table...")
        try:
            row = self.expense_types_page.wait_for_expense_type_in_table(self.expense_name, timeout=15000)
            print(f"Successfully created and found expense type: {self.expense_name}")
            return row
        except Exception as e:
            print(f"Failed to find expense type '{self.expense_name}' in table")
            self._print_table_contents()
            raise
    
    def _print_table_contents(self):
        """Helper method to print current table contents for debugging"""
        try:
            # Refresh the table
            self.page.reload()
            self.page.wait_for_load_state("networkidle")
            
            # Get all rows and print them
            rows = self.page.locator("table tbody tr").all()
            print(f"\nCurrent expense types in table (total: {len(rows)}):")
            
            for i, row in enumerate(rows[:10], 1):  # Print first 10 rows to avoid too much output
                try:
                    text = row.text_content().strip()
                    print(f"{i}. {text}")
                except Exception as e:
                    print(f"Error reading row {i}: {e}")
            
            if len(rows) > 10:
                print(f"... and {len(rows) - 10} more rows")
                
        except Exception as e:
            print(f"Error printing table contents: {str(e)}")
            print(f"Error: {str(e)}")
            # Screenshot functionality has been disabled as per user request
            # self.page.screenshot(path="debug_expense_not_found.png")
            raise
        yield

    def test_basic_search(self):
        """Test basic search functionality with exact match"""
        self.expense_types_page.search_expense_type(self.expense_name)
        self.expense_types_page.wait_for_loading_animation_to_disappear()
        rows = self.page.locator("table tbody tr")
        assert rows.count() > 0, "No results found for exact match"
        
        # Clear any existing search
        self.expense_types_page.clear_search()
        self.expense_types_page.wait_for_loading_animation_to_disappear()
        
        # Search for the full expense name
        print(f"Searching for full name: {self.expense_name}")
        self.expense_types_page.search(self.expense_name)
        
        # Wait for search results to load
        self.expense_types_page.wait_for_loading_animation_to_disappear()
        
        # Refresh the table to ensure we have the latest data
        self.page.wait_for_timeout(1000)  # Small delay for UI to update
        
        # Verify the expense type is in the search results
        assert self.expense_types_page.is_item_in_table(self.expense_name), \
            f"Expense type '{self.expense_name}' not found in search results"
        
        print("✓ Successfully found expense type by full name")

    def test_search_by_partial_name(self):
        """Test searching by partial expense type name"""
        print(f"\n--- Testing search by partial name: '{self.partial_name}' ---")
        
        # Clear any existing search
        self.expense_types_page.clear_search()
        self.expense_types_page.wait_for_loading_animation_to_disappear()
        
        # Search for part of the expense name
        print(f"Searching for partial name: {self.partial_name}")
        self.expense_types_page.search(self.partial_name)
        
        # Wait for search results to load
        self.expense_types_page.wait_for_loading_animation_to_disappear()
        
        # Refresh the table to ensure we have the latest data
        self.page.wait_for_timeout(1000)  # Small delay for UI to update
        
        # Verify the expense type is in the search results
        assert self.expense_types_page.is_item_in_table(self.expense_name), \
            f"Expense type with partial name '{self.partial_name}' not found in search results"
        
        print("✓ Successfully found expense type by partial name")

    def test_search_case_insensitive(self):
        """Test that search is case insensitive"""
        # Create a version of the name with mixed case
        mixed_case = ''.join(
            c.upper() if i % 2 == 0 else c.lower() 
            for i, c in enumerate(self.expense_name)
        )
        
        print(f"\n--- Testing case-insensitive search for: '{mixed_case}' ---")
        
        # Clear any existing search
        self.expense_types_page.clear_search()
        self.expense_types_page.wait_for_loading_animation_to_disappear()
        
        # Search with mixed case
        print(f"Searching with mixed case: {mixed_case}")
        self.expense_types_page.search(mixed_case)
        
        # Wait for search results to load
        self.expense_types_page.wait_for_loading_animation_to_disappear()
        
        # Refresh the table to ensure we have the latest data
        self.page.wait_for_timeout(1000)  # Small delay for UI to update
        
        # Verify the expense type is in the search results
        assert self.expense_types_page.is_item_in_table(self.expense_name), \
            f"Case insensitive search failed for '{mixed_case}'"
        
        print("✓ Successfully found expense type with case-insensitive search")

    def test_search_non_existent(self):
        """Test searching for a non-existent expense type"""
        non_existent = f"NON_EXISTENT_{self.unique_id}"
        print(f"\n--- Testing search for non-existent: '{non_existent}' ---")
        
        # Clear any existing search
        self.expense_types_page.clear_search()
        self.expense_types_page.wait_for_loading_animation_to_disappear()
        
        # Search for a non-existent expense type
        print(f"Searching for non-existent: {non_existent}")
        self.expense_types_page.search(non_existent)
        
        # Wait for search results to load
        self.expense_types_page.wait_for_loading_animation_to_disappear()
        
        # Wait a moment for any potential results to appear
        self.page.wait_for_timeout(1000)
        
        # Verify no results are shown
        try:
            assert not self.expense_types_page.is_item_in_table(non_existent, timeout=2000), \
                f"Unexpected result found for non-existent expense type '{non_existent}'"
        except Exception:
            # If we get here, the item was found when it shouldn't be
            self._print_table_contents()
            raise
            
        # Verify the 'No expense types found' message is shown in the table
        no_data_cell = self.page.locator("td[data-slot='table-cell']:has-text('No expense types found')")
        assert no_data_cell.is_visible(timeout=2000), "'No expense types found' message not shown"
        
        print("✓ Correctly handled search for non-existent expense type")

    def test_clear_search(self):
        """Test clearing the search shows all expense types"""
        print("\n--- Testing clear search functionality ---")
        
        # First search for something specific
        print(f"Initial search for: {self.expense_name}")
        self.expense_types_page.search(self.expense_name)
        
        # Wait for search results to load
        self.expense_types_page.wait_for_loading_animation_to_disappear()
        
        # Verify we have results
        assert self.expense_types_page.is_item_in_table(self.expense_name), \
            f"Expense type '{self.expense_name}' not found after search"
        
        # Clear the search
        print("Clearing search...")
        self.expense_types_page.clear_search()
        self.expense_types_page.wait_for_loading_animation_to_disappear()
        
        # Wait for the table to update after clearing search
        self.page.wait_for_selector("table[data-slot='table']", state='visible')
        
        # Verify the search field is empty using the correct locator
        search_input = self.page.get_by_placeholder("Search expense types...")
        search_input.wait_for(state="visible", timeout=5000)
        
        # Get the current value of the search input
        current_search = search_input.input_value()
        assert current_search == "", f"Search field was not cleared. Current value: '{current_search}'"
        
        # Wait for the table to update with all results
        self.page.wait_for_selector("table[data-slot='table']", state='visible')
        
        # Verify the table shows multiple results (indicating all results are shown)
        data_rows = self.page.locator("table tbody tr:not(:has-text('No expense types found'))")
        assert data_rows.count() > 1, "Expected multiple expense types after clearing search"
        
        print("✓ Search was successfully cleared and all expense types are shown")

    @pytest.mark.flaky(reruns=3, reruns_delay=2)
    def test_search_after_edit(self):
        """Test search works after editing an expense type
        
        This test is marked as flaky and will be retried up to 3 times with a 2-second delay
        between retries if it fails due to timing or visibility issues.
        """
        # Use the expense type created in setup()
        new_expense_name = self.expense_name
        # Generate a completely different name that doesn't contain the original text
        updated_name = f"Modified-{int(time.time())}"
        
        # First, search for the expense type we just created
        self.expense_types_page.search_expense_type(new_expense_name)
        
        # Verify we have exactly one result
        rows = self.page.locator("table tbody tr")
        assert rows.count() == 1, f"Expected 1 result for {new_expense_name}, found {rows.count()}"
        
        # Click the three dots menu on the first (and only) row
        menu_button = rows.first.locator("button[aria-haspopup='menu']")
        menu_button.wait_for(state='visible')
        menu_button.first.click()
        
        # Click the Edit button in the menu
        # Using the exact role and text for the menu item
        self.page.get_by_role("menuitem", name="Edit").click()
        
        # Wait for the edit modal to appear
        modal = self.expense_types_page.get_modal_edit_expense_type()
        modal.wait_for(state='visible')
        
        # Fill the form with the updated name and submit
        self.expense_types_page.fill_name_field(updated_name)
        self.expense_types_page.submit_edit_form()

        # Wait for the loading animation to disappear
        self.expense_types_page.wait_for_loading_animation_to_disappear()
                
        # Clear any existing search
        self.expense_types_page.clear_search()
        
        # Search for the updated name
        self.expense_types_page.search_expense_type(updated_name)
        
        # Wait for the search results to update
        self.page.wait_for_selector("table[data-slot='table']", state='visible')
        self.page.wait_for_selector("table tbody tr", state='visible')
        
        # Get the first row's text content using the exact DOM structure
        first_cell = self.page.locator("table tbody tr:first-child td[data-slot='table-cell'] div.font-medium")
        first_cell.wait_for(state='visible')
        first_cell_text = first_cell.text_content()
        
        # Verify the content
        assert first_cell_text == updated_name, \
            f"Expected '{updated_name}' but found '{first_cell_text}' in first result"

        # Now search for the old name - should not be found
        self.expense_types_page.search_expense_type(new_expense_name)
        
        # Wait for the search to complete and table to update
        self.page.wait_for_selector("table[data-slot='table']", state='visible')
        
        # Get all visible rows that contain expense data (excluding any "no results" rows)
        data_rows = self.page.locator("table tbody tr:not(:has-text('No expense types found'))")
        
        # Verify no rows match the old name
        found_old_name = False
        for i in range(data_rows.count()):
            row_text = data_rows.nth(i).text_content()
            if new_expense_name.lower() in row_text.lower():
                found_old_name = True
                break

        assert not found_old_name, f"Old name '{new_expense_name}' should not be found after edit"
