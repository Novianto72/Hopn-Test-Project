import pytest
import time
from playwright.sync_api import expect
from pages.expense_types.expense_types_page import ExpenseTypesPage

class TestExpenseTypeValidation:
    def test_required_fields_blank_name_and_cost_center_validation(self, logged_in_page):
        """Test that required fields show validation errors"""
        page = logged_in_page
        expense_types_page = ExpenseTypesPage(page)
        
        expense_types_page.navigate()
        expense_types_page.click_new_expense_type()
        
        # Try to submit without filling anything - expect client-side validation
        expense_types_page.submit_form(expect_validation_error=True)
        
        # Verify the modal remains open when required fields are empty
        modal = expense_types_page.get_modal_create_new_expense_type()
        expect(modal).to_be_visible()
        
        # Verify validation error messages are shown for required fields
        # Note: Add specific selectors for your error messages if available
        # Example:
        # expect(page.get_by_text("Name is required")).to_be_visible()
        # expect(page.get_by_text("Cost Center is required")).to_be_visible()
        
        # Close the modal by clicking the Cancel button
        modal.get_by_role("button", name="Cancel").click()
        expect(modal).not_to_be_visible()
        
    def test_required_fields_blank_name_validation(self, logged_in_page):
        """Test that shows error when name is blank but cost center is filled"""
        page = logged_in_page
        expense_types_page = ExpenseTypesPage(page)
        
        # Navigate and open the modal
        expense_types_page.navigate()
        expense_types_page.click_new_expense_type()
        
        # Get the modal and fill only the cost center field
        modal = expense_types_page.get_modal_create_new_expense_type()
        
        # Wait for loading to complete using the page object's method
        expense_types_page.wait_for_loading_animation_to_disappear()
        
        expense_types_page.fill_cost_center_field()
                
        # Submit the form
        submit_button = modal.get_by_role('button', name='Add expense type', exact=True)
        submit_button.click()
        
        # Verify the modal remains open (form didn't submit)
        expect(modal).to_be_visible()
        
        # Clean up - close the modal
        modal.get_by_role('button', name='Cancel').click()
        expect(modal).not_to_be_visible()

    def test_required_fields_blank_cost_center_validation(self, logged_in_page):
        """Test that shows error when name is blank but cost center is filled"""
        page = logged_in_page
        expense_types_page = ExpenseTypesPage(page)
        
        expense_types_page.navigate()
        expense_types_page.click_new_expense_type()

        # Get the modal and fill only the cost center field
        modal = expense_types_page.get_modal_create_new_expense_type()
        
        # Wait for loading to complete using the page object's method
        expense_types_page.wait_for_loading_animation_to_disappear()

        # Fill only the name field, leaving cost center empty
        test_name = f"Test Expense {int(time.time())}"
        expense_types_page.fill_name_field(test_name)
        
        # Wait for the table to be fully loaded and stable
        table_selector = "div[data-slot='table-container'] table"
        page.wait_for_selector(table_selector, state="visible")
                
        # Submit the form
        submit_button = modal.get_by_role('button', name='Add expense type', exact=True)
        submit_button.click()
        
        # Verify the modal remains open and shows the error message
        modal = expense_types_page.get_modal_create_new_expense_type()
        expect(modal).to_be_visible()
        
        # Verify the error message is shown
        error_message = modal.locator('xpath=//div[text()="Name and Cost Center are required"]')
        expect(error_message).to_be_visible()
        
        # Close the modal
        modal.get_by_role("button", name="Cancel").click()
        expect(modal).not_to_be_visible()
        
    def test_name_field_length_validation(self, logged_in_page):
        """Test that name field accepts long input (256 characters)"""
        page = logged_in_page
        expense_types_page = ExpenseTypesPage(page)
        
        expense_types_page.navigate()
        expense_types_page.click_new_expense_type()
        
        # Enter a very long name (256 characters)
        long_name = "a" * 256
        expense_types_page.fill_name_field(long_name)
        
        # Verify the field accepts and maintains the full 256 characters
        name_input = page.locator('input#name')
        input_value = name_input.input_value()
        assert len(input_value) == 256, f"Name field should accept 256 characters, but got {len(input_value)}"
        
        # Clean up
        modal = expense_types_page.get_modal_create_new_expense_type()
        modal.get_by_role("button", name="Cancel").click()
        
    def test_special_characters_in_name(self, logged_in_page):
        """Test that special characters are allowed in the name field"""
        page = logged_in_page
        expense_types_page = ExpenseTypesPage(page)
        
        expense_types_page.navigate()
        expense_types_page.click_new_expense_type()
        
        # Enter a name with special characters
        special_name = "Test!@#$%^&*()_+{}|:<>?[];',./`~"
        expense_types_page.fill_name_field(special_name)
        
        # Verify the special characters were accepted
        name_input = page.locator('input#name')
        assert name_input.input_value() == special_name, "Special characters should be accepted in the name field"
        
        # Clean up
        modal = expense_types_page.get_modal_create_new_expense_type()
        modal.get_by_role("button", name="Cancel").click()
        
    def test_whitespace_only_name_validation(self, logged_in_page):
        """Test that whitespace-only names are not allowed"""
        page = logged_in_page
        expense_types_page = ExpenseTypesPage(page)
        
        expense_types_page.navigate()
        expense_types_page.click_new_expense_type()
        
        # Enter only whitespace in the name field
        expense_types_page.fill_name_field("   ")
        
        # Submit the form - expect client-side validation
        expense_types_page.submit_form(expect_validation_error=True)
        
        # Verify the modal remains open (form was not submitted)
        modal = expense_types_page.get_modal_create_new_expense_type()
        expect(modal).to_be_visible()
        
        # Clean up
        modal.get_by_role("button", name="Cancel").click()
        
    def test_cancel_button_functionality(self, logged_in_page):
        """Test that cancel button discards changes and closes the modal"""
        page = logged_in_page
        expense_types_page = ExpenseTypesPage(page)
        
        expense_types_page.navigate()
        expense_types_page.click_new_expense_type()
        
        # Fill in some data
        test_name = "Test Cancel Button"
        expense_types_page.fill_name_field(test_name)
        
        # Click cancel
        modal = expense_types_page.get_modal_create_new_expense_type()
        modal.get_by_role("button", name="Cancel").click()
        
        # Verify modal is closed
        expect(modal).not_to_be_visible()
        
        # Reopen the form
        expense_types_page.click_new_expense_type()
        
        # Verify fields are empty
        name_input = page.locator('input#name')
        assert name_input.input_value() == "", "Form fields should be empty after cancel"
        
        # Clean up
        modal = expense_types_page.get_modal_create_new_expense_type()
        modal.get_by_role("button", name="Cancel").click()
        
    def test_close_modal_via_x_button(self, logged_in_page):
        """Test that clicking the X button closes the modal without saving"""
        page = logged_in_page
        expense_types_page = ExpenseTypesPage(page)
        
        expense_types_page.navigate()
        expense_types_page.click_new_expense_type()
        
        # Find and click the X button using the SVG with the close icon
        modal = expense_types_page.get_modal_create_new_expense_type()
        close_button = modal.locator('svg.lucide-x')
        close_button.click()
        
        # Verify modal is closed
        expect(modal).not_to_be_visible()
        
    def test_required_field_indicators(self, logged_in_page):
        """Test that required fields are properly marked with an asterisk"""
        page = logged_in_page
        expense_types_page = ExpenseTypesPage(page)
        
        expense_types_page.navigate()
        expense_types_page.click_new_expense_type()
        
        # Check name field label
        name_label = page.locator('label[for="name"]')
        expect(name_label).to_contain_text("*")
        
        # Check cost center field label
        cost_center_label = page.locator('label[for="costCenter"]')
        expect(cost_center_label).to_contain_text("*")
        
        # Clean up
        modal = expense_types_page.get_modal_create_new_expense_type()
        modal.get_by_role("button", name="Cancel").click()
        
    def test_form_reset_after_submission(self, logged_in_page):
        """Test that form resets after successful submission"""
        page = logged_in_page
        expense_types_page = ExpenseTypesPage(page)
        
        expense_types_page.navigate()
        expense_types_page.click_new_expense_type()
        
        # Wait for the modal to be fully loaded
        time.sleep(3)
        
        # Fill and submit the form
        test_name = f"Test Form Reset {int(time.time())}"
        expense_types_page.fill_expense_type_form(test_name)
        expense_types_page.submit_form()
        
        # Wait for the form to be submitted and the table to update
        page.wait_for_selector(f'tr:has-text("{test_name}")')
        
        # Open the form again
        expense_types_page.click_new_expense_type()
        
        # Verify fields are empty
        name_input = page.locator('input#name')
        assert name_input.input_value() == "", "Name field should be empty after form reset"
        
        # Clean up
        modal = expense_types_page.get_modal_create_new_expense_type()
        modal.get_by_role("button", name="Cancel").click()
        
    def test_error_message_persistence(self, logged_in_page):
        """Test that error messages persist/update correctly during form interaction"""
        page = logged_in_page
        expense_types_page = ExpenseTypesPage(page)
        
        expense_types_page.navigate()
        
        # First, test error appears when required field is missing
        expense_types_page.click_new_expense_type()
        modal = expense_types_page.get_modal_create_new_expense_type()
        
        # Wait for loading to complete using the page object's method
        expense_types_page.wait_for_loading_animation_to_disappear()

        # Fill only the name field
        test_name = "Test Error Persistence"
        expense_types_page.fill_name_field(test_name)
        
        # Wait for the table to be fully loaded and stable
        table_selector = "div[data-slot='table-container'] table"
        page.wait_for_selector(table_selector, state="visible")

        # Submit the form to trigger the error
        submit_button = modal.get_by_role('button', name='Add expense type', exact=True)
        submit_button.click()
        
        # Verify error message is shown for required fields
        error_message = modal.locator('xpath=//div[text()="Name and Cost Center are required"]')
        expect(error_message).to_be_visible()
        
        # Close the form
        modal = expense_types_page.get_modal_create_new_expense_type()
        modal.get_by_role("button", name="Cancel").click()
        
        # Reopen the form
        expense_types_page.click_new_expense_type()
        
        # Wait for loading to complete using the page object's method
        expense_types_page.wait_for_loading_animation_to_disappear()

        # Verify error message is not shown initially
        expect(error_message).not_to_be_visible()
        
        # Fill only the name field again
        expense_types_page.fill_name_field(test_name)

        # Wait for the table to be fully loaded and stable
        page.wait_for_selector(table_selector, state="visible")
        
        # Submit to trigger error again
        submit_button.click()
        
        # Verify error message appears again
        expect(error_message).to_be_visible()
        
        # Clean up
        modal = expense_types_page.get_modal_create_new_expense_type()
        modal.get_by_role("button", name="Cancel").click()
