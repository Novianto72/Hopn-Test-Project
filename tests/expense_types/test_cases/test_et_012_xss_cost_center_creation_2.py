"""
Optimized test cases for XSS protection in Expense Type creation form (Cost Center field).
This is an optimized version of test_et_012_xss_cost_center_creation.py for performance comparison.
"""
import pytest
from playwright.sync_api import expect
from pages.expense_types.expense_types_page import ExpenseTypesPage
from pages.cost_centers.cost_centers_page import CostCentersPage
import time

class TestOptimizedExpenseTypeXSSCostCenterCreation:
    """Optimized test cases for XSS protection in Cost Center field."""
    
    @pytest.fixture(scope="function")
    def xss_payloads(self):
        """Test payloads for XSS testing."""
        return [
            # Basic script tags
            "<script>alert('XSS')</script>",
            # Event handlers
            "<img src='x' onerror='alert(1)'>",
            # JavaScript URIs
            "javascript:alert('XSS')",
            # Mixed content
            "Test<script>alert(1)</script>Name",
        ]

    @pytest.fixture(scope="function")
    def test_setup(self, logged_in_page):
        """Test setup with logged in page and page objects."""
        page = logged_in_page
        expense_types_page = ExpenseTypesPage(page)
        cost_centers_page = CostCentersPage(page)
        
        # Navigate to expense types page
        expense_types_page.navigate()
        page.wait_for_load_state("domcontentloaded")
        
        yield page, expense_types_page, cost_centers_page
        
        # Cleanup after test
        try:
            cost_centers_page.navigate()
            page.wait_for_load_state("domcontentloaded")
        except Exception as e:
            print(f"Cleanup warning: {str(e)}")

    def _create_test_cost_center(self, page, cost_centers_page, name):
        """Helper to create a cost center with proper waits and debugging."""
        print(f"\n=== Creating cost center: {name} ===")
        try:
            # Navigate to cost centers
            print("Navigating to cost centers page...")
            cost_centers_page.navigate()
            page.wait_for_load_state("networkidle")
            
            # Click new cost center button
            print("Clicking 'New Cost Center' button...")
            new_button = page.get_by_role("button", name="New Cost Center")
            new_button.wait_for(state="visible", timeout=10000)
            new_button.click()
            
            # Wait for the form to be ready
            print("Waiting for form to be ready...")
            name_field = page.get_by_label("Name")
            name_field.wait_for(state="visible", timeout=10000)
            
            # Fill the form
            print(f"Filling name field with: {name}")
            name_field.fill("")  # Clear any existing value
            name_field.fill(name)
            
            # Small delay for any validation
            page.wait_for_timeout(1000)
            
            # Check for validation errors
            error_messages = page.locator(".error-message, [role='alert'], .Mui-error")
            if error_messages.count() > 0:
                errors = [msg.inner_text() for msg in error_messages.all()]
                print(f"  ⚠️ Validation errors: {errors}")
            
            # Handle Client ID if present
            try:
                client_id_field = page.get_by_label("Client ID")
                if client_id_field.is_visible():
                    print("Filling Client ID field...")
                    client_id_field.fill("test-client")
                    page.wait_for_timeout(500)
            except Exception as e:
                print(f"  ⚠️ Warning when handling Client ID: {str(e)}")
            
            # Take a screenshot before submission for debugging
            page.screenshot(path=f"test-results/cost_center_before_submit_{name[:10]}.png")
            
            # Submit the form
            print("Submitting the form...")
            submit_button = page.get_by_role("button", name="Add Cost Center")
            submit_button.click()
            
            # Check for success or error
            try:
                # First check for success message
                success_selector = "text=Cost Center created"
                page.wait_for_selector(success_selector, state="visible", timeout=10000)
                print(f"  ✓ Cost Center created: {name}")
                return True
            except Exception as e:
                # Check for error messages if success not found
                error_messages = page.locator(".error-message, [role='alert'], .Mui-error")
                if error_messages.count() > 0:
                    errors = [msg.inner_text() for msg in error_messages.all()]
                    print(f"  ✗ Form submission errors: {errors}")
                else:
                    print("  ✗ Failed to create cost center (no error message found)")
                
                # Take a screenshot of the error state
                page.screenshot(path=f"test-results/cost_center_error_{name[:10]}.png")
                return False
            
        except Exception as e:
            print(f"  ❌ Unexpected error in _create_test_cost_center: {str(e)}")
            import traceback
            traceback.print_exc()
            # Take a screenshot of the error state
            page.screenshot(path=f"test-results/cost_center_exception_{name[:10]}.png")
            return False

    @pytest.mark.parametrize("payload, expected_behavior", [
        ("<script>alert('XSS')</script>", "reject"),
        ("<img src='x' onerror='alert(1)'>", "reject"),
        ("javascript:alert('XSS')", "reject"),
        ("Test<script>alert(1)</script>Name", "reject"),
    ])
    def test_xss_in_cost_center_dropdown(self, test_setup, payload, expected_behavior):
        """Test that XSS payloads are properly handled in cost center creation."""
        page, expense_types_page, cost_centers_page = test_setup
        test_expense_name = f"XSS Test {payload[:20]}..."
        safe_cc_name = f"XSS-{int(time.time())}"  # Create a safe name for the test
        
        try:
            print(f"\n=== Testing XSS payload: {payload} ===")
            
            # First, create a safe cost center to ensure the test environment works
            print("Creating a safe cost center for testing...")
            assert self._create_test_cost_center(page, cost_centers_page, safe_cc_name), \
                   f"Failed to create safe cost center for testing"
            
            # Now try to create a cost center with the XSS payload
            print(f"Attempting to create cost center with payload: {payload}")
            creation_successful = self._create_test_cost_center(page, cost_centers_page, f"XSS-{payload}")
            
            if expected_behavior == "reject":
                # The creation should fail for XSS payloads
                assert not creation_successful, f"XSS payload was not rejected: {payload}"
                print(f"✓ XSS payload was correctly rejected: {payload}")
                return
                
            # If we expected the creation to succeed, continue with the rest of the test
            assert creation_successful, f"Failed to create cost center with payload: {payload}"
            
            # Test expense type creation
            print("Testing expense type creation...")
            expense_types_page.navigate()
            expense_types_page.click_new_expense_type()
            
            # Wait for form to be ready
            page.wait_for_selector("input#name:not([disabled])", state="visible", timeout=10000)
            
            # Fill form
            name_field = page.get_by_label("Name")
            name_field.fill("")  # Clear any existing value
            name_field.fill(test_expense_name)
            
            # Handle Cost Center dropdown
            print("Opening cost center dropdown...")
            cost_center_dropdown = page.get_by_label("Cost Center")
            cost_center_dropdown.wait_for(state="visible", timeout=10000)
            cost_center_dropdown.click()
            
            # Wait for dropdown options to appear
            print("Waiting for dropdown options...")
            page.wait_for_selector("[role='listbox']", state="visible", timeout=10000)
            
            # Verify the option is not present (since it should have been rejected)
            print("Verifying XSS payload is not in dropdown...")
            option = page.get_by_role("option", name=f"XSS-{payload}", exact=False)
            assert not option.is_visible(), f"XSS payload appeared in dropdown: {payload}"
            
            # Verify the safe cost center is present
            print("Verifying safe cost center is present...")
            safe_option = page.get_by_role("option", name=safe_cc_name, exact=True)
            assert safe_option.is_visible(), "Safe cost center not found in dropdown"
            
            print(f"✓ XSS test passed for payload: {payload}")
            
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            # Take screenshot on failure
            page.screenshot(path=f"test-results/xss_test_failure_{payload[:10]}.png")
            raise
            
            # Click the option
            option.click()
            
            # Verify the selection was made
            selected_value = cost_center_dropdown.input_value()
            assert selected_value, "No value selected in Cost Center dropdown"
            
            # Verify no XSS execution
            with pytest.raises(Exception) as exc_info:
                with page.expect_event("dialog", timeout=1000) as dialog_info:
                    # If we get here, an alert was triggered
                    dialog = dialog_info.value
                    pytest.fail(f"XSS payload executed: {payload}. Dialog: {dialog.message}")
                    
            # Verify the page is still stable
            assert page.title(), "Page became unresponsive after XSS test"
            
        finally:
            # Cleanup
            try:
                cost_centers_page.navigate()
                if hasattr(cost_centers_page, 'is_item_in_table') and cost_centers_page.is_item_in_table(cc_name):
                    cost_centers_page.delete_item(cc_name)
            except Exception as e:
                print(f"Cleanup warning: {str(e)}")
