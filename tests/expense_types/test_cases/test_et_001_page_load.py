import pytest
from playwright.sync_api import expect
from pages.expense_types.expense_types_page import ExpenseTypesPage

EXPENSE_TYPES_URL = "https://wize-invoice-dev-front.octaprimetech.com/expense-type"

class TestExpenseTypesPageLoad:
    def test_page_loads_correctly(self, logged_in_page):
        """Test that the expense types page loads with all elements"""
        page = logged_in_page
        expense_types_page = ExpenseTypesPage(page)
        
        # Navigate to the expense types page
        expense_types_page.navigate()
        
        # Verify the page title
        expect(page).to_have_title("Invoice AI")
        
        # Verify the main heading
        expect(page.get_by_role("heading", name="Expense Types")).to_be_visible()
        
        # Verify the new button is present
        expect(page.get_by_role("button", name="New Expense Type")).to_be_visible()
        
        # Verify the search input is present
        expect(page.get_by_placeholder("Search expense types...")).to_be_visible()
