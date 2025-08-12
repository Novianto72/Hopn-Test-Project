import pytest
from playwright.sync_api import expect
from pages.expense_types.expense_types_page import ExpenseTypesPage

class TestCancelButton:
    def test_cancel_button_closes_modal(self, logged_in_page):
        """Test that the cancel button closes the modal without saving"""
        page = logged_in_page
        expense_types_page = ExpenseTypesPage(page)
        
        expense_types_page.navigate()
        expense_types_page.click_new_expense_type()
        
        # Get the new expense type modal and click cancel
        modal = expense_types_page.get_modal_create_new_expense_type()
        modal.get_by_role("button", name="Cancel").click()
        
        # Verify modal is closed
        expect(modal).not_to_be_visible()
        
        # Verify no new expense type was created
        expect(page.get_by_text("Expense type created successfully")).not_to_be_visible()
