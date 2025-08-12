import pytest
from playwright.sync_api import expect, Page
from pages.cost_centers.cost_centers_page import CostCentersPage
from tests.config.test_config import URLS
from dataInput.cost_centers.test_data import (
    credentials,
    edit_delete_test_data
)

@pytest.mark.cost_centers
class TestEditDeleteOptions:
    """Test cases for Cost Center edit and delete options in the action menu."""
    
    # Get test data from centralized location
    test_data = edit_delete_test_data
    
    @pytest.fixture(autouse=True)
    def setup(self, logged_in_page: Page):
        """Setup for edit/delete tests."""
        self.page = logged_in_page
        self.cost_centers_page = CostCentersPage(logged_in_page)
        
        # Navigate to cost centers page
        self.page.goto(URLS["COST_CENTERS"])
        self.page.wait_for_selector(
            "h1:has-text('Cost Centers')",
            state="visible",
            timeout=self.test_data["timeouts"]["element_visibility"]
        )
        return self
    
    def test_triple_dot_menu_options(self):
        """TC-EDT-001: Verify triple-dot menu has edit and delete options."""
        menu_options = self.test_data["menu_options"]
        
        # Get the first row's triple dot menu button
        triple_dot_button = self.page.locator(
            "button[aria-haspopup='menu']:has(svg.lucide-ellipsis)"
        ).first
        
        # Click the triple dot button to open the menu
        triple_dot_button.click()
        
        # Wait for the menu to be visible
        menu = self.page.locator("div[role='menu']")
        expect(menu).to_be_visible(
            timeout=self.test_data["timeouts"]["element_visibility"]
        )
        
        # Verify Edit option is visible and has correct text
        edit_option = menu.get_by_role("menuitem", name=menu_options["edit"]["name"])
        expect(edit_option).to_be_visible()
        expect(edit_option).to_have_text(menu_options["edit"]["name"])
        
        # Verify Delete option is visible, has correct text and red color
        delete_option = menu.get_by_role("menuitem", name=menu_options["delete"]["name"])
        expect(delete_option).to_be_visible()
        expect(delete_option).to_have_text(menu_options["delete"]["name"])
        
        # Check if the element has the expected class
        delete_class = delete_option.get_attribute('class')
        assert menu_options["delete"]["button_class"] in delete_class, \
            f"Delete button should have {menu_options['delete']['button_class']} class"
        
        # Click outside to close the menu (cleanup)
        self.page.mouse.click(0, 0)
        print("✓ Verified triple-dot menu contains Edit and Delete options")

    def test_edit_option_clickable(self):
        """Verify that the Edit option in the menu is clickable."""
        # Get the first row's triple dot menu button
        triple_dot_button = self.page.locator(
            "button[aria-haspopup='menu']:has(svg.lucide-ellipsis)"
        ).first
        
        # Click the triple dot button to open the menu
        triple_dot_button.click()
        
        # Click the Edit option
        edit_option = self.page.get_by_role("menuitem", name="Edit").first
        edit_option.click()
        
        # Verify the edit modal is shown
        # Wait for the modal to be visible
        modal = self.page.locator("div[data-slot='card']")
        expect(modal).to_be_visible()
        
        # Check the modal title
        modal_title = modal.locator("div[data-slot='card-title']")
        expect(modal_title).to_contain_text("Edit Cost Center")
        
        # Check the description
        modal_description = modal.locator("div[data-slot='card-description']")
        expect(modal_description).to_contain_text("Fill in the details")
        
        # Verify the name field is present
        name_field = modal.get_by_label("Name")
        expect(name_field).to_be_visible()
        
        # Verify action buttons
        cancel_button = modal.get_by_role("button", name="Cancel")
        submit_button = modal.get_by_role("button", name="Edit cost center")
        expect(cancel_button).to_be_visible()
        expect(submit_button).to_be_visible()
        
        # Close the modal using the X button
        close_button = modal.locator("svg.lucide-x").first
        if close_button.is_visible():
            close_button.click()
        
        # Wait for modal to be hidden
        expect(modal).to_be_hidden()
        
        print("✓ Verified Edit option opens the edit modal with a form")
        
    # Note: Delete functionality test would typically be in a separate test case
    # as it requires additional confirmation and cleanup
    
    def test_edit_existing_cost_center(self):
        """TC-EDT-002: Verify editing an existing cost center updates the record."""
        import random
        # Generate a random 7-digit number
        random_suffix = random.randint(1000000, 9999999)
        updated_name = f"test_update_{random_suffix}"
        
        try:
            # Get the first row and its name before editing
            first_row = self.page.locator("tbody tr").first
            original_name = first_row.locator("td:first-child div").text_content().strip()
            
            print(f"Original cost center name: {original_name}")
            
            # Click the triple dot button to open the menu
            first_row.locator("button[aria-haspopup='menu']").click()
            
            # Click the Edit option
            self.page.get_by_role("menuitem", name="Edit").click()
            
            # Wait for the edit modal and update the name
            modal = self.page.locator("div[data-slot='card']")
            name_field = modal.get_by_label("Name")
            
            # Clear the existing name and type the new one
            name_field.clear()
            name_field.fill(updated_name)
            
            # Submit the form
            modal.get_by_role("button", name="Edit cost center").click()
            
            # Wait for any success message or page update
            self.page.wait_for_timeout(1000)  # Small delay for the update to process
            
            # Verify the first row's name has been updated
            first_row_after_edit = self.page.locator("tbody tr").first
            updated_name_in_table = first_row_after_edit.locator("td:first-child div").text_content().strip()
            
            assert updated_name_in_table == updated_name, \
                f"Expected updated name to be '{updated_name}' but got '{updated_name_in_table}'"
            
            print(f"✓ Successfully updated cost center from '{original_name}' to '{updated_name}'")
        finally:
            # Clean up - revert the cost center name back to original
            first_row = self.page.locator("tbody tr").first
            first_row.locator("button[aria-haspopup='menu']").click()
            
            # Click the Edit option
            self.page.get_by_role("menuitem", name="Edit").click()
            
            # Wait for the edit modal and revert the name
            modal = self.page.locator("div[data-slot='card']")
            name_field = modal.get_by_label("Name")
            
            # Clear the existing name and type the original one back
            name_field.clear()
            name_field.fill(original_name)
            
            # Submit the form
            modal.get_by_role("button", name="Edit cost center").click()
            
            # Wait for any success message or page update
            self.page.wait_for_timeout(1000)  # Small delay for the update to process
            
            # Verify the first row's name is back to original
            first_row_after_edit = self.page.locator("tbody tr").first
            name_in_table = first_row_after_edit.locator("td:first-child div").text_content().strip()
            
            assert name_in_table == original_name, \
                f"Expected name to be reverted to '{original_name}' but got '{name_in_table}'"            
            
            print(f"✓ Successfully reverted cost center name back to '{original_name}'")
            
    def test_delete_cost_center(self):
        """TC-EDT-003: Verify deleting an existing cost center removes it from the list."""
        import random
        import time
        
        try:
            # Generate a unique name for the test cost center
            timestamp = int(time.time())
            test_cost_center_name = f"Test_Delete_{timestamp}"
            
            print(f"\n=== Creating test cost center: {test_cost_center_name} ===")
            
            # Create a new cost center for testing
            # Click the New Cost Center button
            self.page.get_by_role("button", name="New Cost Center").click()
            
            # Wait for the modal to appear
            modal = self.page.locator("div[data-slot='card']")
            expect(modal).to_be_visible()
            
            # Fill in the name field
            name_field = modal.get_by_label("Name")
            name_field.fill(test_cost_center_name)
            
            # Submit the form
            time.sleep(3)
            modal.get_by_role("button", name="Add cost center").click()
            
            # Wait for the success message and refresh
            self.page.wait_for_selector(f"text='{test_cost_center_name}'", timeout=10000)
            print(f"✓ Created test cost center: {test_cost_center_name}")
            
            # Verify the new cost center is in the list (should be first)
            first_row = self.page.locator("tbody tr").first
            first_row_name = first_row.locator("td:first-child div").text_content().strip()
            
            if first_row_name != test_cost_center_name:
                # If not first, try to find it in the table
                rows = self.page.locator("tbody tr").all()
                found = False
                for row in rows:
                    if row.locator("td:first-child div").text_content().strip() == test_cost_center_name:
                        found = True
                        # Move the row to the top by clicking on it (if needed)
                        row.click()
                        break
                
                if not found:
                    raise AssertionError(f"Test cost center '{test_cost_center_name}' not found in the list")
            
            print("\n--- Starting deletion test ---")
            
            # Click the triple dot menu for the first row
            first_row = self.page.locator("tbody tr").first
            first_row.locator("button[aria-haspopup='menu']").click()
            
            # Set up a dialog handler to accept the confirmation
            def handle_dialog(dialog):
                print(f"Dialog message: {dialog.message}")
                dialog.accept()  # Clicks 'OK' or 'Delete' on the dialog
            
            # Listen for the dialog before clicking delete
            self.page.on('dialog', handle_dialog)
            
            # Click the Delete option
            self.page.get_by_role("menuitem", name="Delete").click()
            
            # Wait for the dialog to be handled and the deletion to complete
            self.page.wait_for_timeout(1000)  # Small delay for the update
            
            print("✓ Deletion confirmed via dialog")
            
            # Verify the cost center is no longer in the list
            first_row_after_delete = self.page.locator("tbody tr").first
            new_first_row_name = first_row_after_delete.locator("td:first-child div").text_content().strip()
            
            assert new_first_row_name != test_cost_center_name, \
                f"Cost center '{test_cost_center_name}' still appears in the list after deletion"
                
            print(f"✓ Verified cost center '{test_cost_center_name}' was successfully deleted")
            
        except Exception as e:
            # Screenshot functionality has been disabled as per user request
            # self.page.screenshot(path="delete_cost_center_failure.png")
            # print("Screenshot saved as 'delete_cost_center_failure.png'")
            raise e
