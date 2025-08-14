"""Test cases for XSS protection in Expense Type creation form (Cost Center field)."""
import pytest
from playwright.sync_api import expect, Browser, BrowserContext
from pages.expense_types.expense_types_page import ExpenseTypesPage
from pages.cost_centers.cost_centers_page import CostCentersPage
import time

class TestExpenseTypeXSSCostCenterCreation:
    """Test cases for XSS protection in Expense Type creation form (Cost Center field)."""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, logged_in_page):
        """Setup and teardown for each test."""
        self.page = logged_in_page
        self.expense_types_page = ExpenseTypesPage(self.page)
        self.cost_centers_page = CostCentersPage(self.page)
        
        # List of XSS payloads to test in cost center names
        self.xss_payloads = [
            # Basic script tags
            "<script>alert('XSS')</script>",
            "<script>alert(String.fromCharCode(88,83,83))</script>",
            
            # Event handlers
            "<img src='x' onerror='alert(1)'>",
            "<svg onload='alert(1)'>",
            "<body onload=alert('XSS')>",
            
            # JavaScript URIs
            "javascript:alert('XSS')",
            "JaVaScRiPt:alert('XSS')",  # Case variation
            "javascript:alert(document.cookie)",
            
            # Mixed content
            "Test<script>alert(1)</script>Name",
            "<h1>Cost Center</h1><script>alert(1)</script>",
            "<b>Important</b> Center<script>alert(1)</script>",
            
            # HTML5 vectors
            "<details/open/ontoggle=alert('XSS')>",
            "<video><source onerror=alert('XSS')>",
            "<input onfocus=alert('XSS') autofocus>",
            
            # Special cases
            "${alert('XSS')}",  # Template literal
            "{{7*7}}"  # Template injection
        ]
        
        # We'll create cost centers one at a time in the test
        self.created_cost_centers = []
        
        # Setup: Create a normal cost center for testing
        self.normal_cost_center_name = f"Test Cost Center {int(time.time())}"
        self._create_normal_cost_center()
        
        # Navigate to expense types page
        self.expense_types_page.navigate()
        
        # Setup complete
        yield
        
        # Teardown - ensure clean state after all tests
        try:
            # Navigate to cost centers page to clean up
            self.cost_centers_page.navigate()
            
            # Delete all test cost centers
            for cc_name in self.created_cost_centers:
                if self.cost_centers_page.is_item_in_table(cc_name):
                    self.cost_centers_page.delete_item(cc_name)
                    
            # Delete the test cost center if it exists
            if self.cost_centers_page.is_item_in_table(self.normal_cost_center_name):
                self.cost_centers_page.delete_item(self.normal_cost_center_name)
                
        except Exception as e:
            print(f"Teardown warning: {str(e)}")
    

    
    def _create_cost_center(self, name):
        """Helper method to create a cost center with proper waits"""
        print(f"Creating cost center: {name}")
        self.page.get_by_role("button", name="New Cost Center").click()
        
        # Wait for the form to be ready
        self.page.wait_for_selector("input#name:not([disabled])", state="visible", timeout=10000)
        
        # Fill the form with a small delay between actions
        self.page.get_by_label("Name").fill(name)
        self.page.wait_for_timeout(1000)  # Wait for any validation
        
        # Handle Client ID if needed
        try:
            client_id_field = self.page.get_by_label("Client ID")
            if client_id_field.is_visible():
                client_id = "test-client"  # Replace with a valid client ID if needed
                client_id_field.fill(client_id)
                print(f"  Filled Client ID: {client_id}")
                self.page.wait_for_timeout(500)
        except Exception as e:
            print(f"  Warning when handling Client ID: {str(e)}")
        
        # Submit the form
        self.page.get_by_role("button", name="Add Cost Center").click()
        
        # Wait for success or error
        try:
            # Check for success message first
            success_selector = "text=Cost Center created"
            self.page.wait_for_selector(success_selector, state="visible", timeout=10000)
            print(f"  ✓ Cost Center created: {name}")
            return True
        except:
            # Check for error message
            error_message = self.page.locator(".error-message, [role=alert], .text-destructive, .ant-message-error").first
            if error_message.is_visible():
                error_text = error_message.inner_text()
                print(f"  ✗ Failed to create cost center: {error_text}")
            return False

    def test_xss_in_cost_center_dropdown(self):
        """
        ET-012: Verify that XSS attempts in the Cost Center dropdown are properly handled
        when creating a new expense type.
        """
        # Set up JavaScript error monitoring
        self.page.on("pageerror", lambda err: print(f"Page error: {err}"))
        self.page.on("console", lambda msg: print(f"Console {msg.type}: {msg.text}"))
        
        # Process one payload at a time
        for i, cc_name in enumerate(self.xss_payloads):
            test_start_time = time.time()
            test_expense_name = f"XSS Test {int(test_start_time)}-{i}"
            # Use the raw payload as the cost center name
            cc_test_name = cc_name
            
            # Clear any existing test data before starting
            self.expense_types_page.navigate()
            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_timeout(1000)
            print(f"\n=== Testing XSS payload {i+1}: {cc_name} ===")
            
            try:
                # 1. First, navigate to Cost Centers and create a test cost center with the current payload
                print("Navigating to Cost Centers...")
                self.cost_centers_page.navigate()
                self.page.wait_for_load_state("networkidle")
                self.page.wait_for_timeout(1000)  # Additional wait for page to stabilize
                
                # Create the cost center using our helper method
                if not self._create_cost_center(cc_test_name):
                    # If creation failed, log and skip to next payload
                    print(f"Skipping payload '{cc_name}' due to cost center creation failure")
                    continue
                    
                # Wait a moment for the UI to update
                self.page.wait_for_timeout(1500)
                
                # 2. Now navigate to Expense Types to create a new expense type
                print("Navigating to Expense Types...")
                self.expense_types_page.navigate()
                self.page.wait_for_load_state("networkidle")
                
                # Open a new expense type form
                print("Opening new expense type form...")
                self.expense_types_page.click_new_expense_type()
                
                # Wait for the form to be fully loaded and ready
                self.page.wait_for_selector("input#name:not([disabled])", state="visible", timeout=10000)
                
                # Fill in a normal name
                print(f"Filling expense name: {test_expense_name}")
                name_field = self.page.get_by_label("Name")
                name_field.fill("")  # Clear any existing value
                name_field.fill(test_expense_name)
                
                # Add a small delay to ensure the form is ready
                self.page.wait_for_timeout(1000)
                
                # Select the cost center we just created
                print("Selecting cost center from dropdown...")
                dropdown = self.page.get_by_label("Cost Center")
                dropdown.wait_for(state="visible", timeout=10000)
                dropdown.click()
                
                # Wait for dropdown options to be visible
                self.page.wait_for_selector("[role='listbox']", state="visible", timeout=10000)
                
                # Find and click the option with the cost center name
                print(f"  Looking for cost center option: {cc_test_name}")
                option = self.page.get_by_role("option", name=cc_test_name, exact=True)
                option.wait_for(state="visible", timeout=10000)
                
                # Scroll the option into view if needed
                option.scroll_into_view_if_needed()
                option.click()
                
                # Verify the selection was made
                selected_value = dropdown.input_value()
                print(f"  Selected cost center value: {selected_value}")
                
                # Submit the form
                print("Submitting form...")
                submit_button = self.page.get_by_role("button", name="Add Expense Type")
                submit_button.wait_for(state="visible", timeout=10000)
                submit_button.click()
                
                # Wait for success message or error
                try:
                    # Check for success message with a longer timeout
                    success_message = self.page.get_by_text("Expense Type created", exact=False)
                    success_message.wait_for(state="visible", timeout=10000)
                    print("✓ Expense Type created successfully")
                    
                    # Wait for the table to update
                    self.page.wait_for_selector("table tr:last-child td:first-child", state="visible", timeout=10000)
                    
                    # Get the displayed values from the table
                    expense_name_cell = self.page.locator("table tr:last-child td:first-child")
                    expense_cc_cell = self.page.locator("table tr:last-child td:nth-child(2)")
                    
                    displayed_expense_name = expense_name_cell.inner_text()
                    displayed_cc_name = expense_cc_cell.inner_text()
                    
                    print(f"  Created Expense Type: {displayed_expense_name}")
                    print(f"  With Cost Center: {displayed_cc_name}")
                    
                    # Verify the cost center name is properly escaped in the table
                    if any(char in cc_name for char in ['<', '>', '"', "'", '&']):
                        # Check that HTML special characters are escaped
                        assert any(entity in displayed_cc_name for entity in ['&lt;', '&gt;', '&quot;', '&#39;', '&amp;']), \
                            f"Cost Center name not properly escaped. Expected HTML entities, got: {displayed_cc_name}"
                        
                        # Verify no raw HTML/JavaScript in the output
                        assert "<script>" not in displayed_cc_name.lower(), f"Script tags not properly escaped: {displayed_cc_name}"
                        assert "<img" not in displayed_cc_name.lower(), f"Image tags not properly escaped: {displayed_cc_name}"
                        assert "<svg" not in displayed_cc_name.lower(), f"SVG tags not properly escaped: {displayed_cc_name}"
                        assert "javascript:" not in displayed_cc_name.lower(), f"JavaScript protocol not properly escaped: {displayed_cc_name}"
                    
                    # Verify the original payload is not directly in the output
                    assert cc_name not in displayed_cc_name, f"Original XSS payload found in output: {displayed_cc_name}"
                    
                    # Verify no JavaScript was executed
                    js_was_executed = self.page.evaluate("""() => {
                        return window.xssExecuted || false;
                    }""")
                    assert not js_was_executed, "JavaScript from XSS payload was executed"
                    
                except Exception as e:
                    # If no success message, check for error message
                    error_message = self.page.locator(".error-message, [role=alert], .text-destructive, .ant-message-error").first
                    if error_message.is_visible():
                        error_text = error_message.inner_text()
                        print(f"✓ Input rejected with message: {error_text}")
                    else:
                        # Take a screenshot and log page content for debugging
                        self.page.screenshot(path=f"test-results/et_xss_cc_test_failure_{i}.png")
                        print("Page content:", self.page.content()[:1000])
                        raise AssertionError(f"No success or error message detected for payload: {cc_name}")
                
            except Exception as e:
                # Take a screenshot and log page content before re-raising
                error_suffix = str(int(time.time()))[-6:]
                self.page.screenshot(path=f"test-results/et_xss_cc_test_error_{i}_{error_suffix}.png")
                print("Error occurred, page content:", self.page.content()[:1000])
                print(f"Current URL: {self.page.url}")
                raise AssertionError(f"Test failed for payload '{cc_name}': {str(e)}")
                
            finally:
                # Clean up test data - handle one item at a time
                try:
                    print("\n=== Cleaning up test data ===")
                    
                    # 1. Clean up expense type if it was created
                    if 'displayed_expense_name' in locals() and displayed_expense_name:
                        print(f"  Deleting test expense type: {displayed_expense_name}")
                        try:
                            # Navigate to expense types if not already there
                            if "expense-type" not in self.page.url:
                                self.expense_types_page.navigate()
                                self.page.wait_for_load_state("networkidle")
                            
                            # Wait for the page to be ready
                            self.page.wait_for_selector("table tbody tr", state="visible", timeout=10000)
                            
                            # Delete the expense type
                            self.expense_types_page.delete_item(displayed_expense_name)
                            print("  ✓ Expense type deleted")
                            
                            # Wait for the deletion to complete
                            self.page.wait_for_timeout(1000)
                            
                        except Exception as e:
                            print(f"  Warning: Failed to delete expense type: {str(e)}")
                            # Take a screenshot for debugging
                            self.page.screenshot(path=f"test-results/cleanup_error_expense_{i}.png")
                    
                    # 2. Clean up the test cost center we created
                    if 'cc_test_name' in locals() and cc_test_name:
                        print(f"  Deleting test cost center: {cc_test_name}")
                        try:
                            # Navigate to cost centers
                            self.cost_centers_page.navigate()
                            self.page.wait_for_load_state("networkidle")
                            self.page.wait_for_timeout(1000)  # Additional wait for page to stabilize
                            
                            # Wait for the search input to be ready
                            search_box = self.page.get_by_placeholder("Search")
                            search_box.wait_for(state="visible", timeout=10000)
                            
                            # Clear any existing search
                            search_box.fill("")
                            search_box.press("Enter")
                            self.page.wait_for_timeout(500)
                            
                            # Search for the cost center by name
                            search_box.fill(cc_test_name)
                            search_box.press("Enter")
                            
                            # Wait for search results with a longer timeout
                            self.page.wait_for_selector("table tbody tr", state="visible", timeout=15000)
                            
                            # Check if the cost center exists
                            row_selector = f"tr:has-text('{cc_test_name}')"
                            if self.page.locator(row_selector).count() > 0:
                                # Click the delete button for this row
                                delete_btn = self.page.locator(f"{row_selector} button[aria-label^='Delete']").first
                                delete_btn.click()
                                
                                # Wait for and confirm deletion
                                confirm_btn = self.page.get_by_role("button", name="Delete", exact=True)
                                confirm_btn.wait_for(state="visible", timeout=5000)
                                confirm_btn.click()
                                
                                # Wait for success message
                                try:
                                    self.page.wait_for_selector("text=Cost Center deleted", timeout=10000)
                                    print("  ✓ Cost center deleted")
                                except:
                                    print("  ✓ Cost center deletion initiated (success not confirmed)")
                            else:
                                print("  ✓ Cost center not found (may have been deleted)")
                                
                        except Exception as e:
                            print(f"  Warning: Failed to delete cost center: {str(e)}")
                            # Take a screenshot for debugging
                            self.page.screenshot(path=f"test-results/cleanup_error_cc_{i}.png")
                    
                    # 3. Navigate back to expense types page for the next test
                    print("  Preparing for next test...")
                    self.expense_types_page.navigate()
                    self.page.wait_for_load_state("networkidle")
                    self.page.wait_for_timeout(1500)  # Additional wait for page to stabilize
                    
                except Exception as cleanup_error:
                    print(f"  Warning: Error during cleanup: {str(cleanup_error)}")
                    # Take a screenshot for debugging
                    self.page.screenshot(path=f"test-results/cleanup_error_{i}.png")
                    # Even if cleanup fails, we should continue with the next test
                    continue
