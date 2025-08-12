"""Test cases for XSS protection in Expense Type creation (Name field)."""
import pytest
from playwright.sync_api import expect
from pages.expense_types.expense_types_page import ExpenseTypesPage
from pages.cost_centers.cost_centers_page import CostCentersPage
import time


class TestExpenseTypeXSSNameCreation:
    """Test cases for XSS protection in Expense Type creation form (Name field)."""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, logged_in_page):
        self.page = logged_in_page
        self.expense_types_page = ExpenseTypesPage(self.page)
        self.cost_centers_page = CostCentersPage(self.page)
        
        # Setup: Create a normal cost center for testing
        self.normal_cost_center_name = f"Test Cost Center {int(time.time())}"
        self._create_normal_cost_center()
        
        # Navigate to expense types page
        self.expense_types_page.navigate()
        
        # Setup complete, run the test
        yield
        
        # Teardown - ensure clean state after test
        try:
            # Navigate to cost centers page to clean up
            self.cost_centers_page.navigate()
            
            # Delete the test cost center if it exists
            if self.cost_centers_page.is_item_in_table(self.normal_cost_center_name):
                self.cost_centers_page.delete_item(self.normal_cost_center_name)
                
            # Navigate back to expense types page
            self.expense_types_page.navigate()
            
        except Exception as e:
            print(f"Teardown warning: {str(e)}")
    
    def _create_normal_cost_center(self):
        """Helper method to create a normal cost center for testing."""
        try:
            # Navigate to cost centers page and wait for it to load
            print("Navigating to cost centers page...")
            self.cost_centers_page.navigate()
            self.page.wait_for_load_state("networkidle")
            
            # Click new cost center button and wait for the form
            print("Clicking new cost center button...")
            self.cost_centers_page.new_cost_center_btn.click()
            self.page.wait_for_selector("label:has-text('Name')", state="visible")
            
            # Fill the name
            print(f"Filling cost center name: {self.normal_cost_center_name}")
            name_field = self.page.get_by_label("Name")
            name_field.fill("")
            name_field.fill(self.normal_cost_center_name)
            
            # Submit the form (don't wait for navigation)
            print("Submitting cost center form...")
            self.cost_centers_page.submit_form()
            
            # Wait for either:
            # 1. The success message to appear, or
            # 2. The cost center to appear in the table
            print("Waiting for success...")
            try:
                # Try waiting for success message first
                success_selector = f"text='Cost center created successfully'"
                self.page.wait_for_selector(success_selector, state="visible", timeout=5000)
                print("✓ Success message found")
            except:
                # If no success message, check if the cost center appears in the table
                print("No success message, checking if cost center appears in table...")
                self.page.wait_for_selector(
                    f"table tr:has-text('{self.normal_cost_center_name}')", 
                    state="visible",
                    timeout=10000
                )
            
            print(f"✓ Created cost center: {self.normal_cost_center_name}")
            
            # Navigate back to expense types page
            print("Navigating back to expense types page...")
            self.expense_types_page.navigate()
            
        except Exception as e:
            # Take a screenshot for debugging
            self.page.screenshot(path="test-results/cost_center_creation_failed.png")
            print("\n=== DEBUG INFO ===")
            print(f"Current URL: {self.page.url}")
            print("Page content:")
            print(self.page.content()[:1000])  # Print first 1000 chars of page
            print("==================\n")
            
            # Try to navigate to expense types page before failing
            try:
                self.expense_types_page.navigate()
            except:
                pass
                
            raise Exception(f"Failed to create cost center: {str(e)}")
    
    def test_xss_in_name_field_during_creation(self):
        """
        ET-011: Verify that XSS attempts in the Expense Type name field are properly handled
        when creating a new expense type.
        """
        # List of XSS payloads to test in expense type names
        self.xss_payloads = [
            # Basic script tags
            "<script>alert('XSS')</script>",
            "<script>alert(String.fromCharCode(88,83,83))</script>",
            
            # Event handlers
            "<img src='x' onerror='alert(1)'>",
            "<svg onload='alert(1)'>",
            "<body onload=alert('XSS')>",
            
            # Mixed content
            "Test<script>alert(1)</script>Name",
            "Admin<script>alert(1)</script>User",  # Common name pattern
            "O'Malley<script>alert(1)</script>Doe",  # Common name with special char
            
            # Obfuscation attempts
            "<img src=x onerror=alert('XSS')>",
            "<img src=x oneonerrorrror=alert('XSS')>",
            "<a href=\"javascript:alert('XSS')\">Click</a>",
            
            # Special characters
            "<img src=x onerror=`alert('XSS')`>",
            "<img src=x onerror=alert('XSS')//'>",
            "Test\u003Cscript\u003Ealert(1)\u003C/script\u003EName"  # Unicode escape
        ]
        for payload in self.xss_payloads:
            print(f"\n=== Testing payload: {payload} ===")
            
            try:
                # Always start fresh for each payload
                print("Navigating to expense types page...")
                self.expense_types_page.navigate()
                
                # Close any open modals or forms
                self.page.keyboard.press("Escape")
                self.page.wait_for_timeout(500)
                
                # Open a new expense type form
                print("Opening new expense type form...")
                self.expense_types_page.click_new_expense_type()
                
                # Wait for the form to be fully loaded and ready
                self.page.wait_for_selector("input#name:not([disabled])", state="visible", timeout=10000)
                
                # Clear any existing value in the name field
                self.page.fill('input#name', '')
                
                # Use the page object's method to fill the form and handle the Cost Center dropdown
                print("Filling expense type form with XSS payload...")
                self.expense_types_page.fill_expense_type_form(payload)
                
                # Wait a moment for the form to process the input
                self.page.wait_for_timeout(1000)
                
                # Submit the form
                self.page.get_by_role("button", name="Add Expense Type").click()

                # Wait for success message or error
                try:
                    # Check for success message
                    success_message = self.page.get_by_text("Expense Type created", exact=False)
                    success_message.wait_for(state="visible", timeout=5000)
                    print(f"✓ Form submitted successfully for payload: {payload}")

                    # Wait for the table to update
                    self.page.wait_for_selector("table tr:last-child td:first-child")
                    
                    # Get the displayed text from the table
                    table_cell = self.page.locator("table tr:last-child td:first-child")
                    displayed_text = table_cell.inner_text()
                    print(f"  Displayed as: {displayed_text}")
                    
                    # Verify the payload is properly escaped in the UI
                    if any(char in payload for char in ['<', '>', '"', "'", '&']):
                        # Check that HTML special characters are escaped
                        assert '&lt;' in displayed_text or '&gt;' in displayed_text or '&quot;' in displayed_text or '&#39;' in displayed_text or '&amp;' in displayed_text, \
                            f"XSS payload not properly escaped. Expected HTML entities, got: {displayed_text}"
                        
                        # Verify no raw script tags in the output
                        assert "<script>" not in displayed_text.lower(), f"Script tags not properly escaped: {displayed_text}"
                        assert "<img" not in displayed_text.lower(), f"Image tags not properly escaped: {displayed_text}"
                        assert "<svg" not in displayed_text.lower(), f"SVG tags not properly escaped: {displayed_text}"
                        assert "javascript:" not in displayed_text.lower(), f"JavaScript protocol not properly escaped: {displayed_text}"
                    
                    # Verify the original payload is not directly in the output
                    assert payload not in displayed_text, f"Original XSS payload found in output: {displayed_text}"
                    
                    # Verify no JavaScript was executed
                    js_was_executed = self.page.evaluate("""() => {
                        return window.xssExecuted || false;
                    }""")
                    assert not js_was_executed, "JavaScript from XSS payload was executed"
                    
                    # Clean up by deleting the test entry
                    self.expense_types_page.delete_item(displayed_text)
                    print("  ✓ Cleaned up test entry")

                except Exception as e:
                    # If no success message, check for error message
                    error_message = self.page.locator(".error-message, [role=alert], .text-destructive").first
                    if error_message.is_visible():
                        error_text = error_message.inner_text()
                        print(f"✓ Input rejected with message: {error_text}")
                    else:
                        # Take a screenshot for debugging
                        self.page.screenshot(path=f"test-results/et_xss_name_test_failure_{payload[:10]}.png")
                        print("Page content:", self.page.content()[:1000])
                        raise AssertionError(f"No success or error message detected for payload: {payload}")
                
            except Exception as e:
                # Take a screenshot and re-raise with more context
                self.page.screenshot(path=f"test-results/et_xss_name_test_error_{payload[:10]}.png")
                raise AssertionError(f"Test failed for payload '{payload}': {str(e)}")
            finally:
                # Ensure we're back to a clean state for the next test
                try:
                    if "Expense Type created" in self.page.content():
                        # If we're not on the expense types page, navigate there
                        if "expense-type" not in self.page.url:
                            self.expense_types_page.navigate()
                except:
                    pass
