"""
Test case to verify that creating a cost center after searching doesn't cause frontend errors.
"""
import time
import pytest
from playwright.sync_api import Page, expect
from pages.cost_centers.cost_centers_page import CostCentersPage
from tests.config.test_config import URLS
from dataInput.cost_centers.test_data import credentials

class TestSearchThenCreateCostCenter:
    """Tests for creating a cost center after searching for a non-existing one."""
    
    @pytest.fixture(autouse=True)
    def setup(self, logged_in_page: Page):
        """Setup test environment before each test."""
        self.page = logged_in_page
        self.cost_centers_page = CostCentersPage(self.page)
        
        # Generate unique test cost center name
        self.timestamp = int(time.time())
        self.test_cost_center_name = f"TestCostCenter_{self.timestamp}"
        self.created_cost_centers = []  # Track created cost centers for cleanup
        
        # Navigate to cost centers page
        self.page.goto(URLS["COST_CENTERS"], wait_until="networkidle")
        
        yield
        
        # Cleanup: Delete created cost centers
        self._cleanup_created_cost_centers()
    
    def _cleanup_created_cost_centers(self):
        """Helper method to clean up created cost centers."""
        for cost_center_name in self.created_cost_centers:
            try:
                self.cost_centers_page.navigate()
                if self.cost_centers_page.is_item_in_table(cost_center_name):
                    self.cost_centers_page.delete_item(cost_center_name)
            except Exception as e:
                print(f"Cleanup warning: Failed to delete cost center '{cost_center_name}': {str(e)}")
    
    def _create_cost_center(self, name):
        """Helper method to create a cost center."""
        print(f"Creating cost center: {name}")
        
        try:
            # Click the New Cost Center button using the page object method
            if not self.cost_centers_page.click_new_cost_center():
                print("  ✗ Failed to click New Cost Center button")
                return False, ""
            
            # Wait for the modal to be fully visible
            #modal_selector = "div[role='dialog']"
            #self.page.wait_for_selector(modal_selector, state="visible", timeout=10000)
            
            # Wait for the form to be interactive
            name_field = self.page.locator("input#name")
            name_field.wait_for(state="visible", timeout=10000)
            
            # Clear and fill the name field
            name_field.fill("")
            name_field.fill(name)
            
            # Handle Client ID if present
            try:
                client_id_field = self.page.locator("input#client_id")
                if client_id_field.is_visible():
                    client_id_field.fill("test-client")
            except Exception as e:
                print(f"  Warning when handling Client ID: {str(e)}")
            
            # Submit the form
            submit_button = self.page.locator("button:has-text('Add Cost Center')")
            submit_button.click()
            
            # Wait a moment for any potential error to appear
            self.page.wait_for_timeout(2000)  # 2 seconds
            
            # Check for the specific error message in any h2 element
            error_message = "Application error: a client-side exception has occurred"
            all_h2s = self.page.query_selector_all("h2")
            
            for h2 in all_h2s:
                try:
                    if error_message in h2.inner_text():
                        # Take a screenshot for debugging
                        self.page.screenshot(path="test-results/error_detected.png")
                        return False, f"Frontend error detected: {h2.inner_text()}"
                except:
                    continue
                    
            return True, ""
            
        except Exception as e:
            error_msg = f"Failed to create cost center: {str(e)}"
            print(f"  ✗ {error_msg}")
            # Take a screenshot for debugging
            self.page.screenshot(path=f"test-results/error_creating_cost_center_{name}.png")
            return False, error_msg
    
    def _close_any_modals(self):
        """Helper to close any open modals or overlays."""
        try:
            # Look for common modal close buttons and click them
            close_selectors = [
                "button[aria-label='Close']",
                ".modal-close",
                "button:has-text('Close')",
                "button:has-text('Cancel')",
                ".modal-backdrop"
            ]
            
            for selector in close_selectors:
                elements = self.page.query_selector_all(selector)
                for element in elements:
                    if element.is_visible():
                        element.click()
                        self.page.wait_for_timeout(500)  # Give it time to close
        except Exception as e:
            print(f"  Note when checking for modals: {str(e)}")
    
    def test_create_after_search_no_frontend_error(self):
        """
        Test that creating a cost center after searching for a non-existing one
        doesn't cause frontend errors.
        """
        try:
            # Use the same name for both search and creation
            cost_center_name = f"NonExistingCostCenter_{self.timestamp}"
            print(f"Using cost center name: {cost_center_name}")
            
            # Clear any existing search first
            self.cost_centers_page.search("")
            self.page.wait_for_load_state("networkidle")
            
            # Step 1: Search for the non-existing cost center
            print(f"Searching for non-existing cost center: {cost_center_name}")
            self.cost_centers_page.search(cost_center_name)
            
            # Wait for search results to update
            self.page.wait_for_load_state("networkidle")
            
            # Verify no results found using POM locator
            expect(self.cost_centers_page.no_data_message).to_be_visible()
            
            # Additional wait to ensure UI is stable
            self.page.wait_for_timeout(1000)
            
            # Step 2: Create a new cost center with the same name
            success, error_msg = self._create_cost_center(cost_center_name)
            if not success:
                assert False, f"Failed to create cost center: {error_msg}"
            
            # Add to cleanup list
            #self.created_cost_centers.append(cost_center_name)
            
            # Step 3: Check for frontend error immediately after creation
            error_selector = "h2"
            print("\nDebug - Checking for error messages...")
            
            # Take a screenshot for debugging
            self.page.screenshot(path="test-results/debug_before_error_check.png")
            
            # Get all h2 elements and check their text content
            all_h2_elements = self.page.query_selector_all(error_selector)
            print(f"Found {len(all_h2_elements)} h2 elements on the page")
            
            # Check each h2 element for error text
            for i, element in enumerate(all_h2_elements):
                try:
                    text = element.inner_text()
                    print(f"H2 element {i + 1} text: {text[:100]}...")
                    if 'Application error: a client-side exception has occurred' in text:
                        print("\nERROR: Found the error message in an h2 element!")
                        self.page.screenshot(path="test-results/error_found.png")
                        assert False, f"Frontend error detected: {text}"
                except Exception as e:
                    print(f"  Could not get text from h2 element {i + 1}: {str(e)}")
            
            # Also check the entire page content as a fallback
            page_content = self.page.content()
            if 'Application error: a client-side exception has occurred' in page_content:
                print("\nERROR: Found the error message in page content!")
                with open("test-results/page_content.html", "w", encoding="utf-8") as f:
                    f.write(page_content)
                assert False, "Frontend error detected in page content"
            
            print("No error messages found on the page")
                
            # If we get here, no frontend error was detected
            print("  ✓ No frontend errors detected after cost center creation")
            
        except Exception as e:
            # Take a screenshot on failure
            self.page.screenshot(path="test-results/test_failure.png")
            raise
