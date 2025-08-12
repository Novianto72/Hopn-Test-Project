import time
import pytest
from playwright.sync_api import Page, expect
from pages.cost_centers.cost_centers_page import CostCentersPage
from tests.config.test_config import URLS
from dataInput.cost_centers.test_data import (
    credentials,
    multiple_creations_test_data
)


@pytest.mark.cost_centers
class TestMultipleCostCenterCreations:
    """Tests for creating multiple cost centers consecutively."""
    
    # Get test data from centralized location
    test_data = multiple_creations_test_data
    credentials = credentials
    
    @pytest.fixture(autouse=True)
    def setup(self, logged_in_page: Page):
        """Setup test environment before each test."""
        print("\n--- Setting up test environment (browser session started) ---")
        self.page = logged_in_page
        self.cost_centers_page = CostCentersPage(logged_in_page)
        
        # Navigate to cost centers page
        self.page.goto(URLS["COST_CENTERS"])
        self.page.wait_for_selector(
            "h1:has-text('Cost Centers')",
            state="visible",
            timeout=self.test_data["timeouts"]["page_load"]
        )
        return self

    def test_multiple_cost_center_creations(self):
        """TC-CC-010: Verify creating multiple cost centers consecutively."""
        # Get test data
        num_creations = self.test_data["iterations"]
        base_name = self.test_data["base_name"]
        
        for i in range(num_creations):
            print(f"\n--- Test iteration {i + 1}/{num_creations} ---")
            
            # Generate unique name for the cost center
            timestamp = int(time.time())
            cost_center_name = f"{base_name} {timestamp}"
            
            try:
                # --- Create Cost Center ---
                print("Step 1: Creating new cost center")
                new_button = self.page.get_by_role("button", name="New")
                expect(new_button).to_be_visible()
                new_button.click()
                
                # Fill in the form
                modal = self.page.locator("div[data-slot='card']")
                expect(modal).to_be_visible(timeout=10000)
                
                name_field = modal.get_by_label("Name")
                name_field.fill(cost_center_name)
                
                # Submit the form
                time.sleep(3)
                submit_button = modal.get_by_role("button", name="Add cost center")
                submit_button.click()
                
                # Wait for creation to complete
                expect(modal).to_be_hidden(timeout=10000)
                
                # Verify in table
                self.page.wait_for_selector("table tbody tr", state="visible", timeout=10000)
                first_row_name = self.page.locator("table tbody tr:first-child td:first-of-type").first
                expect(first_row_name).to_have_text(cost_center_name, timeout=5000)
                print(f"✓ Created cost center: {cost_center_name}")
                
                # --- Delete Cost Center ---
                print("Step 2: Deleting the cost center")
                # Search for the cost center
                search_input = self.page.get_by_placeholder("Search Cost Centers")
                search_input.fill(cost_center_name)
                self.page.wait_for_timeout(1000)
                
                # Set up the dialog handler before any dialog appears
                dialog_handled = False
                
                def handle_dialog(dialog):
                    nonlocal dialog_handled
                    print(f"Dialog message: {dialog.message}")
                    dialog.accept()  # Clicks 'OK' or 'Delete' on the dialog
                    dialog_handled = True
                
                # Listen for the dialog before clicking delete
                self.page.once('dialog', handle_dialog)
                
                # Click the triple dot menu for the first row
                first_row = self.page.locator("tbody tr").first
                first_row.locator("button[aria-haspopup='menu']").click()
                
                # Click the Delete option
                self.page.get_by_role("menuitem", name="Delete").click()
                
                # Wait for the dialog to be handled
                start_time = time.time()
                while not dialog_handled and (time.time() - start_time) < 5:  # Wait up to 5 seconds
                    self.page.wait_for_timeout(100)
                
                if not dialog_handled:
                    print("Warning: No dialog was handled during deletion")
                
                # Wait for the deletion to complete
                self.page.wait_for_timeout(1000)  # Small delay for the update
                
                print("✓ Deletion confirmed via dialog")
                
                # Clear the search input to show all cost centers
                search_input = self.page.get_by_placeholder("Search Cost Centers")
                search_input.clear()
                self.page.wait_for_timeout(500)  # Wait for search to clear
                
                # Verify the cost center is no longer in the list
                first_row_after_delete = self.page.locator("tbody tr").first
                if first_row_after_delete.is_visible():
                    new_first_row_name = first_row_after_delete.locator("td:first-child div").text_content().strip()
                    assert new_first_row_name != cost_center_name, \
                        f"Cost center '{cost_center_name}' still appears in the list after deletion"
                
                print(f"✓ Verified cost center '{cost_center_name}' was successfully deleted")
                
                # Ensure we're ready for the next iteration
                self.page.wait_for_timeout(1000)  # Additional wait for UI to stabilize
                    
            except Exception as e:
                print(f"❌ Error during test iteration {i+1}: {str(e)}")
                raise
