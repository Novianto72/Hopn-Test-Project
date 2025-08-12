import pytest
import time
from playwright.sync_api import expect, Page
from pages.cost_centers.cost_centers_page import CostCentersPage
from tests.config.test_config import URLS
from dataInput.cost_centers.test_data import (
    required_validation_test_data
)

@pytest.mark.cost_centers
class TestRequiredFieldValidation:
    """Test cases for required field validation in Cost Center form."""
    
    # Get test data from centralized location
    test_data = required_validation_test_data
    
    @pytest.fixture(autouse=True)
    def setup(self, logged_in_page: Page):
        """Setup for validation tests."""
        self.page = logged_in_page
        self.cost_centers_page = CostCentersPage(logged_in_page)
        
        # Navigate to cost centers page
        self.page.goto(URLS["COST_CENTERS"])
        self.page.wait_for_selector(
            "h1:has-text('Cost Centers')",
            state="visible",
            timeout=self.test_data["timeouts"]["modal_visibility"]
        )
        return self
    
    def test_required_field_validation(self):
        """TC-CRT-002: Verify required field validation on 'New Cost Center' form."""
        try:
            modal_data = self.test_data["modal"]
            print("\n=== Starting required field validation test ===")
            
            # Click the New Cost Center button
            self.page.get_by_role("button", name="New Cost Center").click()
            
            # Wait for the modal to appear
            modal = self.page.locator("div[data-slot='card']")
            expect(modal).to_be_visible(
                timeout=self.test_data["timeouts"]["modal_visibility"]
            )
            
            # Verify the modal title is visible and matches expected text
            modal_title = modal.locator("div[data-slot='card-title']")
            expect(modal_title).to_contain_text(modal_data["title"])
            
            # Verify the modal description is visible and matches expected text
            modal_description = modal.locator("div[data-slot='card-description']")
            expect(modal_description).to_contain_text(modal_data["description"])
            
            print("✓ Modal is open with correct title and description")
            
            # Click the submit button without filling in the required fields
            submit_button = modal.get_by_role("button", name=modal_data["buttons"][1])
            submit_button.click()
            
            print("✓ Clicked submit button without filling required fields")
            
            # Wait for validation check with timeout from test data
            self.page.wait_for_timeout(self.test_data["timeouts"]["validation_check"])
            
            # Verify the modal is still open
            expect(modal).to_be_visible()
            
            # Additional verification that we're still on the same form
            expect(modal_title).to_contain_text("New Cost Center")
            
            # Verify the name field is still empty
            name_field = modal.get_by_label("Name")
            expect(name_field).to_have_value("")
            
            print("✓ Verified modal remains open with empty required field")
            
        except Exception as e:
            # Screenshot functionality has been disabled as per user request
            # self.page.screenshot(path="required_validation_failure.png")
            # print("Screenshot saved as 'required_validation_failure.png'")
            raise e
        finally:
            # Clean up by closing the modal if it's still open
            try:
                close_button = modal.locator("svg.lucide-x").first
                if close_button.is_visible():
                    close_button.click()
            except:
                pass
