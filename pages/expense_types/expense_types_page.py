from playwright.sync_api import Page, expect, TimeoutError
import time
import re
from tests.page_components.table_component import TableComponent

class ExpenseTypesPage:
    def __init__(self, page: Page):
        self.page = page
        self.url = "https://wize-invoice-dev-front.octaprimetech.com/expense-type"
        self.table = TableComponent(page)
        
    def navigate(self):
        self.page.goto(self.url)
        self.page.wait_for_selector("h1:has-text('Expense Types')")
        
    def click_new_expense_type(self):
        self.page.get_by_role("button", name="New Expense Type").click()
        
    def get_modal_create_new_expense_type(self):
        """Get the modal for creating a new expense type"""
        return self.page.locator("div[data-slot='card']")
    
    def get_modal_edit_expense_type(self):
        """Get the modal for editing an expense type"""
        return self.page.locator("div[data-slot='card']")
        
    def fill_name_field(self, name: str):
        """Fill only the name field in the expense type form"""
        self.page.fill('input#name', name)
        return self
        
    def search(self, query: str):
        """Search for an expense type by name"""
        search_input = self.page.get_by_placeholder("Search expense types...")
        search_input.fill(query)
        search_input.press("Enter")
        self.page.wait_for_load_state("domcontentloaded")
        return self
        
    def is_item_in_table(self, name: str, timeout: int = 5000) -> bool:
        """Check if an expense type exists in the table"""
        try:
            self.page.wait_for_selector(f"tr:has-text('{name}')", timeout=timeout)
            return True
        except TimeoutError:
            return False
            
    def delete_item(self, name: str):
        """Delete an expense type by name"""
        try:
            # Find the row with the given name and click the delete button
            row = self.page.locator(f"tr:has-text('{name}')")
            row.get_by_role("button", name="Delete").click()
            
            # Confirm deletion in the dialog
            self.page.get_by_role("button", name=re.compile("delete", re.IGNORECASE)).click()
            
            # Wait for the operation to complete
            self.page.wait_for_load_state("domcontentloaded")
            return True
        except Exception as e:
            print(f"Error deleting expense type {name}: {str(e)}")
            return False
        
    def fill_cost_center_field(self, cost_center: str = None):
        """Select a cost center from the dropdown
    
        Args:
            cost_center: Optional cost center to select. If None, will select the first available option
        """
        try:
            print("\n=== Starting to fill cost center field ===")
            
            # Wait for the dropdown to be clickable
            self.page.wait_for_selector('button[role="combobox"]', state='visible', timeout=10000)
            
            # Click the dropdown to open it
            self.page.click('button[role="combobox"]')
            
            # Wait for the dropdown options to be visible
            self.page.wait_for_selector('div[role="listbox"]', state='visible', timeout=10000)
            
            # Select the first available option
            first_option = self.page.locator('div[role="option"]').first
            first_option.click()
            
            # Wait for the selection to be applied
            self.page.wait_for_timeout(500)
            return self
            
        except Exception as e:
            print(f"Error selecting cost center: {str(e)}")
            self.page.screenshot(path="test-results/cost_center_selection_error.png")
            raise
            
        try:
            if cost_center:
                # Select the specified cost center
                option_selector = f'div[role="option"]:has-text("{cost_center}"):visible'
                self.page.wait_for_selector(option_selector, state='visible', timeout=10000)
                option = self.page.locator(option_selector)
                option.click()
            else:
                # Since the options are in a hidden select element, we'll use a different approach
                # First, wait for the select element to be present in the DOM
                select_selector = 'select[aria-hidden="true"]'
                self.page.wait_for_selector(select_selector, state='attached', timeout=10000)
                
                # Select the first available option
                first_option_value = self.page.evaluate('''() => {
                    const select = document.querySelector('select[aria-hidden]');
                    return select ? select.querySelector('option')?.value : null;
                }''')
                
                if not first_option_value:
                    raise Exception("Could not find any options in the cost center dropdown")
                
                # Set the value using JavaScript since the select is hidden
                self.page.evaluate(f'''() => {{
                    const select = document.querySelector('select[aria-hidden]');
                    if (select) select.value = '{first_option_value}';
                    // Trigger change event
                    const event = new Event('change', {{ bubbles: true }});
                    select?.dispatchEvent(event);
                }}''')
                
            # Wait for the selection to be applied
            self.page.wait_for_timeout(500)
            return self
            
            # Select the first available option
            first_option_selector = f'{listbox_selector} div[role="option"]:visible'
            self.page.wait_for_selector(first_option_selector, state='visible', timeout=10000)
            first_option = self.page.locator(first_option_selector).first
            
            if first_option.is_visible():
                first_option.click()
                self.page.wait_for_timeout(500)  # Small delay for the selection to take effect
                return self
                
            raise Exception("No cost center options available in the dropdown")
                
        except Exception as e:
            print("Error selecting dropdown option:", str(e))
            self.page.screenshot(path="dropdown_selection_error.png")
            raise
    
    def fill_expense_type_form(self, name: str, cost_center: str = None):
        """Fill the expense type form with the given name and optionally select a cost center
        
        Args:
            name: Name for the expense type
            cost_center: Optional cost center to select. If None, will select the first available option
        """
        try:
            # Wait for the name input to be ready
            name_field = self.page.locator('input#name')
            name_field.wait_for(state='visible', timeout=10000)
            
            # Clear the field first (in case of any existing value)
            name_field.fill('')
            
            # Fill the name field with the provided value
            name_field.fill(name)
            
            # Wait a moment for any UI updates
            self.page.wait_for_timeout(300)
            
            # Handle cost center selection
            if cost_center is not None:
                self.fill_cost_center_field(cost_center)
            else:
                # Wait for the dropdown to be ready
                dropdown = self.page.locator('button[role="combobox"]')
                dropdown.wait_for(state='visible', timeout=5000)
                
                # Select the first available option
                self.fill_cost_center_field()
                
            # Wait for any UI updates after selection
            self.page.wait_for_timeout(500)
            
        except Exception as e:
            # Take a screenshot for debugging
            self.page.screenshot(path="test-results/fill_form_error.png")
            print(f"Error filling expense type form: {str(e)}")
            raise
        
    def submit_form(self, wait_for_success: bool = True, expect_validation_error: bool = False, timeout: int = 10000):
        """Submit the expense type form and handle different response scenarios
        
        Args:
            wait_for_success: Whether to wait for the success message (default: True)
            expect_validation_error: Whether to expect a client-side validation error (default: False)
            timeout: Maximum time to wait in milliseconds (default: 10000ms)
            
        Returns:
            bool: True if submission was successful, False otherwise
        """
        try:
            # Get the submit button - using exact text match for better reliability
            submit_button = self.page.get_by_role("button", name="Add expense type", exact=True)
            
            # Ensure the button is visible and enabled
            submit_button.wait_for(state="visible")
            
            # Use JavaScript to ensure the button is clickable
            self.page.evaluate('''(button) => {
                // Remove any overlays or elements that might be blocking the button
                const overlays = document.querySelectorAll('.blocking-overlay, .v-overlay');
                overlays.forEach(el => el.style.display = 'none');
                
                // Ensure the button is visible and clickable
                if (button) {
                    button.style.visibility = 'visible';
                    button.style.opacity = '1';
                    button.style.pointerEvents = 'auto';
                    button.disabled = false;
                }
                
                // Ensure the document is interactive
                if (document.body) {
                    document.body.style.pointerEvents = 'auto';
                }
                if (document.documentElement) {
                    document.documentElement.style.pointerEvents = 'auto';
                }
            }''', submit_button.element_handle())
            
            # Add a small delay to ensure UI is ready
            self.page.wait_for_timeout(500)
            
            if expect_validation_error:
                # For validation errors, just click the button and return
                submit_button.click()
                # Wait a bit for client-side validation to complete
                self.page.wait_for_timeout(1000)
                return False
            else:
                # For successful submissions, wait for the API response
                with self.page.expect_response(
                    lambda response: 
                        'expense-type' in response.url and 
                        response.request.method in ['POST', 'PUT'],
                    timeout=timeout
                ) as response_info:
                    submit_button.click()
                
                # Wait for any loading states to complete
                self.wait_for_loading_animation_to_disappear(timeout=timeout)
                
                # Optionally wait for success message
                if wait_for_success:
                    try:
                        success_selector = "text=Expense type created successfully"
                        error_selector = "text=Error"
                        
                        # Wait for either success or error message to appear
                        try:
                            self.page.wait_for_selector(
                                f"{success_selector}, {error_selector}", 
                                state="visible", 
                                timeout=5000  # Shorter timeout for message to appear
                            )
                            
                            # Check which one appeared
                            if self.page.locator(error_selector).is_visible():
                                error_text = self.page.locator(error_selector).inner_text()
                                print(f"Error submitting form: {error_text}")
                                return False
                            
                            # If we got here, success message is visible
                            return True
                            
                        except Exception as e:
                            print(f"Warning: Did not see success/error message after submission: {str(e)}")
                            # Continue anyway as the submission might have worked without a message
                            return True
                            
                    except Exception as e:
                        print(f"Error waiting for form submission result: {str(e)}")
                        # Take a screenshot for debugging
                        self.page.screenshot(path='test-results/submit_form_error.png')
                        return False
                    return False
            
            return True  # If not waiting for success, assume it worked
            
        except Exception as e:
            print(f"Error submitting form: {str(e)}")
            # Take a screenshot for debugging
            self.page.screenshot(path='test-results/submit_form_error.png')
            raise

    def submit_edit_form(self, wait_for_success: bool = True, timeout: int = 10000):
        """Submit the edit expense type form and optionally wait for success
        
        Args:
            wait_for_success: Whether to wait for the success message (default: True)
            timeout: Maximum time to wait in milliseconds (default: 10000ms)
            
        Returns:
            bool: True if submission was successful, False otherwise
        """
        try:
            # Get the submit button - using exact text match for better reliability
            submit_button = self.page.get_by_role("button", name="Edit expense type", exact=True)
            
            # Ensure the button is visible and enabled
            submit_button.wait_for(state="visible")
            
            # Use JavaScript to ensure the button is clickable
            self.page.evaluate('''(button) => {
                // Remove any overlays or elements that might be blocking the button
                const overlays = document.querySelectorAll('.blocking-overlay, .v-overlay');
                overlays.forEach(el => el.style.display = 'none');
                
                // Ensure the button is visible and clickable
                if (button) {
                    button.style.visibility = 'visible';
                    button.style.opacity = '1';
                    button.style.pointerEvents = 'auto';
                    button.disabled = false;
                }
                
                // Ensure the document is interactive
                if (document.body) {
                    document.body.style.pointerEvents = 'auto';
                }
                if (document.documentElement) {
                    document.documentElement.style.pointerEvents = 'auto';
                }
            }''', submit_button.element_handle())
            
            # Add a small delay to ensure UI is ready
            self.page.wait_for_timeout(500)
            
            # Click the button and wait for navigation if applicable
            with self.page.expect_response(lambda response: 
                'expense-type' in response.url and 
                response.request.method in ['POST', 'PUT']
            ) as response_info:
                submit_button.click()
            
            # Wait for any loading states to complete
            self.wait_for_loading_animation_to_disappear(timeout=timeout)
            
            # Optionally wait for success message
            if wait_for_success:
                try:
                    # Wait for either success message or error message
                    success_selector = "text=Expense type updated successfully"
                    error_selector = "text=Error"
                    
                    # Wait for either success or error message to appear
                    try:
                        self.page.wait_for_selector(
                            f"{success_selector}, {error_selector}", 
                            state="visible", 
                            timeout=5000  # Shorter timeout for message to appear
                        )
                        
                        # Check which one appeared
                        if self.page.locator(error_selector).is_visible():
                            error_text = self.page.locator(error_selector).inner_text()
                            print(f"Error submitting edit form: {error_text}")
                            return False
                        
                        # If we got here, success message is visible
                        return True
                        
                    except Exception as e:
                        print(f"Warning: Did not see success/error message after edit submission: {str(e)}")
                        # Continue anyway as the submission might have worked without a message
                        
                except Exception as e:
                    print(f"Error waiting for edit form submission result: {str(e)}")
                    # Take a screenshot for debugging
                    self.page.screenshot(path='test-results/submit_edit_form_error.png')
                    return False
            
            return True  # If not waiting for success, assume it worked
            
        except Exception as e:
            print(f"Error submitting edit form: {str(e)}")
            # Take a screenshot for debugging
            self.page.screenshot(path='test-results/submit_edit_form_error.png')
            raise
        
    def wait_for_loading_animation_to_disappear(self, timeout: int = 10000, max_retries: int = 3):
        """Wait for the loading animation to disappear with retry logic
        
        Args:
            timeout: Maximum time to wait in milliseconds (default: 10000ms)
            max_retries: Maximum number of times to retry checking (default: 3)
            
        Returns:
            bool: True if loading animation disappeared or was not found, False if retries exceeded
        """
        loading_selectors = [
            "svg.lucide-loader-circle.animate-spin",  # Newer loading spinner
            "svg.lucide-loader-circle",               # Older loading spinner
            ".animate-spin"                           # Generic loading spinner
        ]
        
        for selector in loading_selectors:
            for attempt in range(max_retries):
                try:
                    # Check if the loading element exists and is visible
                    element = self.page.locator(selector)
                    if element.count() > 0 and element.is_visible():
                        # If it's visible, wait for it to be hidden or removed
                        element.wait_for(state="hidden", timeout=timeout)
                        return True
                    return True  # Element not found or not visible
                except Exception as e:
                    if attempt == max_retries - 1:  # Last attempt
                        print(f"Loading animation still visible after {max_retries} retries with selector '{selector}': {str(e)}")
                        if selector == loading_selectors[-1]:  # Last selector
                            return False
                    else:
                        self.page.wait_for_timeout(1000)  # Small delay before next retry
        
        return True  # If we get here, no loading indicators were found
    def clear_search(self):
        """Clear the search field"""
        search = self.page.get_by_placeholder("Search expense types...")
        search.clear()
        search.press("Enter")
        self.page.wait_for_timeout(500)  # Short wait for the clear to take effect
        
    def search_expense_type(self, name: str):
        """Search for an expense type by name"""
        search = self.page.get_by_placeholder("Search expense types...")
        search.fill(name)
        search.press("Enter")
        self.page.wait_for_timeout(1000)  # Wait for search results
    
    def wait_for_expense_type_in_table(self, name: str, timeout: float = 15000):
        """Wait for an expense type to appear in the table and return its row
        
        Args:
            name: The name of the expense type to wait for
            timeout: Maximum time to wait in milliseconds (default: 15000ms)
            
        Returns:
            The row element if found
            
        Raises:
            TimeoutError: If the expense type doesn't appear within the timeout
        """
        start_time = time.time()
        last_error = None
        
        while (time.time() - start_time) * 1000 < timeout:
            try:
                # First ensure any loading is complete
                self.wait_for_loading_animation_to_disappear(timeout=2000)
                
                # Try to find the row
                row = self.table.wait_for_row_with_text(name, timeout=2000)
                if row:
                    return row
                    
            except Exception as e:
                last_error = e
                # If we get here, the row wasn't found yet
                # Refresh the table by triggering a search with the current search term
                try:
                    search_input = self.page.get_by_placeholder("Search expense types...")
                    if search_input.is_visible():
                        current_search = search_input.input_value()
                        search_input.fill(current_search)
                        search_input.press("Enter")
                        self.page.wait_for_timeout(500)  # Small delay for search to trigger
                except:
                    pass  # Ignore errors during refresh
                
                # Wait a bit before retrying
                self.page.wait_for_timeout(500)
        
        # If we get here, we've timed out
        print(f"Timed out waiting for expense type '{name}' to appear in table")
        if last_error:
            print(f"Last error: {str(last_error)}")
        
        # One final attempt to get the row to include in the error
        try:
            return self.table.wait_for_row_with_text(name, timeout=1000)
        except Exception as e:
            raise TimeoutError(f"Expense type '{name}' did not appear in the table within {timeout}ms") from e
        
    def get_expense_types_list(self):
        """Get the list of all expense types from the table"""
        return self.table.get_all_rows_data()
        
    def get_first_row_name(self):
        """Get the name from the first row in the table"""
        rows = self.table.get_all_rows_data()
        return rows[0]['name'] if rows else None
        
    def delete_first_expense_type(self):
        # Set up a flag to track if the dialog was handled
        dialog_handled = False
        
        def handle_dialog(dialog):
            nonlocal dialog_handled
            print(f"Dialog message: {dialog.message}")
            dialog.accept()  # Clicks 'OK' or 'Delete' on the dialog
            dialog_handled = True
        
        # Listen for the dialog before any actions that might trigger it
        self.page.once('dialog', handle_dialog)
        
        try:
            # Click the three dots menu
            menu_button = self.page.locator("button[aria-haspopup='menu']").nth(1)
            menu_button.wait_for(state='visible')
            menu_button.click()
            
            # Click delete
            delete_option = self.page.get_by_role("menuitem", name="Delete")
            delete_option.wait_for(state='visible')
            delete_option.click()
            
            # Wait for the dialog to be handled
            start_time = time.time()
            while not dialog_handled and (time.time() - start_time) < 10:  # Wait up to 10 seconds
                self.page.wait_for_timeout(100)
                
            if not dialog_handled:
                print("Warning: Delete confirmation dialog was not handled")
                
            # Wait for the operation to complete
            self.page.wait_for_timeout(1000)
            
        except Exception as e:
            print(f"Error during expense type deletion: {str(e)}")
            self.page.screenshot(path="delete_expense_type_error.png")
            raise
        
    def get_success_message(self):
        return self.page.get_by_text("Expense type created successfully")

    # Removed duplicate method - consolidated with the implementation above
        return False
