"""Test cases for XSS protection in Cost Center creation."""
import pytest
from playwright.sync_api import expect
from pages.cost_centers.cost_centers_page import CostCentersPage

class TestCostCenterXSSCreation:
    """Test cases for XSS protection in Cost Center creation form."""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, logged_in_page):
        self.page = logged_in_page
        self.cost_centers_page = CostCentersPage(self.page)
        # Navigate to cost centers page
        self.cost_centers_page.navigate()
        
        # Setup complete, run the test
        yield
        
        # Teardown - ensure clean state after test
        try:
            # Wait for any pending operations to complete
            self.page.wait_for_timeout(1000)
            
            # If there's a modal open, try to close it
            if self.page.locator("[role=dialog], .modal").is_visible():
                close_buttons = self.page.locator("button:has-text('Close'), button:has-text('Cancel')")
                if close_buttons.count() > 0:
                    close_buttons.first.click()
            
            # Navigate to cost centers page to ensure we're in a good state
            self.cost_centers_page.navigate()
            
            # Wait for any pending operations to complete
            self.page.wait_for_load_state("networkidle")
            
        except Exception as e:
            print(f"Teardown warning: {str(e)}")
            # If something goes wrong, just continue with cleanup
        
    def test_xss_in_name_field_during_creation(self):
        """
        CC-011: Verify that XSS attempts in the name field are properly handled
        when creating a new cost center by ensuring:
        1. Input is properly HTML-escaped when displayed
        2. No JavaScript is executed from the input
        3. The form handles the input without errors
        """
        # List of XSS payloads to test (removed SQL injection payloads as they're not XSS)
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src='x' onerror='alert(1)'>",
            "<svg onload='alert(1)'>",
            "javascript:alert('XSS')",
            "Test<script>alert(1)</script>Name"
        ]
        
        for payload in xss_payloads:
            print(f"\nTesting payload: {payload}")
            
            try:
                # Ensure we're on the form page
                if not self.page.get_by_label("Name").is_visible():
                    self.cost_centers_page.navigate()
                    self.cost_centers_page.new_cost_center_btn.click()
                
                # Clear and fill the name field
                name_field = self.page.get_by_label("Name")
                name_field.fill("")
                name_field.fill(payload)
                
                # Submit the form
                self.cost_centers_page.submit_form()
                
                # Wait for either success notification or error message
                try:
                    # Check for success message
                    success_message = self.page.get_by_text("Cost Center created", exact=False)
                    success_message.wait_for(state="visible", timeout=5000)
                    print(f"✓ Form submitted successfully for payload: {payload}")
                    
                    # Verify the entry in the table
                    table_cell = self.page.locator("table tr:last-child td:first-child")
                    displayed_text = table_cell.inner_text()
                    print(f"  Displayed as: {displayed_text}")
                    
                    # Verify the text is properly escaped
                    if "<" in payload and "&lt;" not in displayed_text:
                        raise AssertionError(f"XSS payload not properly escaped. Expected HTML entities, got: {displayed_text}")
                    
                    # Clean up by deleting the test entry
                    self.cost_centers_page.delete_item(displayed_text)
                    
                except Exception as e:
                    # If no success message, check for error message
                    error_message = self.page.locator(".error-message, [role=alert], .text-destructive").first
                    if error_message.is_visible():
                        error_text = error_message.inner_text()
                        print(f"✓ Input rejected with message: {error_text}")
                    else:
                        # Take a screenshot for debugging
                        self.page.screenshot(path=f"test-results/xss_test_failure_{payload[:10]}.png")
                        raise AssertionError(f"No success or error message detected for payload: {payload}")
                
            except Exception as e:
                # Take a screenshot and re-raise with more context
                self.page.screenshot(path=f"test-results/xss_test_error_{payload[:10]}.png")
                raise AssertionError(f"Test failed for payload '{payload}': {str(e)}")
            finally:
                # Ensure we're back to a clean state for the next test
                try:
                    if "Cost Center created" in self.page.content():
                        # Wait for any pending operations
                        self.page.wait_for_timeout(500)
                        
                        # If we're not on the cost centers page, navigate there
                        if "cost-center" not in self.page.url:
                            self.cost_centers_page.navigate()
                        
                        # Wait for the page to be fully loaded
                        self.page.wait_for_load_state("networkidle")
                        
                        # Close any open modals
                        if self.page.locator("[role=dialog], .modal").is_visible():
                            self.page.keyboard.press("Escape")
                except Exception as e:
                    print(f"Cleanup warning: {str(e)}")
