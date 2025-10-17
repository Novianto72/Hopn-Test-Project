import time
import pytest
from playwright.sync_api import Page, expect
from pages.cost_centers.cost_centers_page import CostCentersPage
from tests.config.test_config import URLS
from dataInput.cost_centers.test_data import credentials, new_button_test_data

class TestNewCostCenterButton:
    """Tests for the New Cost Center button functionality"""
    
    # Get test data from centralized location
    test_data = new_button_test_data
    credentials = credentials
    
    @pytest.fixture(autouse=True)
    def setup(self, logged_in_page: Page):
        """Setup test environment before each test."""
        self.page = logged_in_page
        
        # Generate unique test cost center name
        timestamp = int(time.time())
        self.test_cost_center_name = f"{self.test_data['test_cost_center_name_prefix']} {timestamp}"
        self.created_cost_centers = []  # Track created cost centers for cleanup
        
        # Navigate to cost centers page
        self.page.goto(URLS["COST_CENTERS"], wait_until="domcontentloaded")
        expect(self.page).to_have_url(URLS["COST_CENTERS"])
        
        # Create page object
        self.cost_centers_page = CostCentersPage(self.page)
        
        yield  # This is where the test runs
        
        # Teardown - clean up any created test data
        self._cleanup_test_data()
    
    def _cleanup_test_data(self):
        """Clean up any test data created during the test."""
        if not hasattr(self, 'created_cost_centers') or not self.created_cost_centers:
            return
            
        print("\nCleaning up test data...")
        for cost_center_name in self.created_cost_centers:
            try:
                # Try to find and delete the cost center
                cost_center_row = self.page.get_by_role("row").filter(has_text=cost_center_name).first
                if cost_center_row.is_visible():
                    # Look for delete button in the row
                    delete_button = cost_center_row.get_by_role("button", name="Delete")
                    if delete_button.is_visible():
                        delete_button.click()
                        # Confirm deletion if needed
                        confirm_button = self.page.get_by_role("button", name="Delete").first
                        if confirm_button.is_visible():
                            confirm_button.click()
                            print(f"Deleted cost center: {cost_center_name}")
            except Exception as e:
                print(f"Warning: Failed to clean up cost center '{cost_center_name}': {str(e)}")
    
    def open_new_cost_center_modal(self):
        """Helper method to open the New Cost Center modal."""
        print("\n--- Opening New Cost Center modal ---")
        self.cost_centers_page.click_new_cost_center()
        
        # Wait for modal to appear
        modal = self.page.locator("[role=dialog], .modal, [data-testid=modal], .MuiDialog-root").first
        modal.wait_for(state="visible", timeout=10000)
        
        # Get modal elements
        modal_elements = {
            'title': self.page.get_by_role("heading", name=re.compile("New Cost Center", re.IGNORECASE)).first,
            'name_input': self.page.get_by_label("Name", exact=True).first,
            'add_button': self.page.get_by_role("button", name=re.compile("Add Cost Center|Submit", re.IGNORECASE)).first,
            'cancel_button': self.page.get_by_role("button", name="Cancel").first
        }
        
        return modal_elements
    
    def test_create_new_cost_center(self):
        """CC-004-05: Verify a new cost center can be created."""
        print("\n=== Starting test_create_new_cost_center ===")
        
        # Open the modal
        print("Opening New Cost Center modal")
        modal_elements = self.open_new_cost_center_modal()
        
        # Fill in the name field
        print(f"Setting name to: {self.test_cost_center_name}")
        modal_elements['name_input'].fill(self.test_cost_center_name)
        
        # Submit the form
        print("Submitting the form...")
        modal_elements['add_button'].click()
        
        # Wait for the modal to close (indicating success)
        print("Waiting for modal to close...")
        modal_elements['title'].wait_for(state='hidden', timeout=10000)
        
        # Add the cost center to our cleanup list
        self.created_cost_centers.append(self.test_cost_center_name)
        print(f"Successfully created cost center: {self.test_cost_center_name}")
        
        # Verify the new cost center appears in the list
        print("Verifying cost center appears in the list...")
        expect(self.page.get_by_text(self.test_cost_center_name)).to_be_visible(timeout=5000)
        print("Success! New cost center is visible in the list.")
        
        # Take a screenshot for documentation
        self.page.screenshot(path="cost_center_created.png")
        print("Test completed successfully!")
