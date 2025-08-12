import pytest
from playwright.sync_api import expect
from tests.Invoices.page_object.invoices_page import InvoicesPage

INVOICES_URL = "https://wize-invoice-dev-front.octaprimetech.com/invoices"

class TestInvoicesPageLoad:
    def test_page_loads_correctly(self, logged_in_page):
        """Test that the invoices page loads with all elements"""
        page = logged_in_page
        invoices_page = InvoicesPage(page)
        
        # Navigate to the invoices page
        invoices_page.navigate()
        
        # Verify the page title
        expect(page).to_have_title("Invoice AI")
        
        # Verify the main heading
        expect(page.get_by_role("heading", name="Invoices")).to_be_visible()
        
        # Verify the refresh button is present
        expect(page.get_by_role("button", name="Refresh")).to_be_visible()
        
        # Verify the new invoice button is present
        expect(page.get_by_role("button", name="New Invoice")).to_be_visible()
        
        # Verify the search input is present
        expect(page.get_by_placeholder("Search invoices..."))
        
        # Verify the total invoices counter is present
        expect(page.locator("div.text-sm.font-medium.text-gray-500:has-text('Total Invoices') + div.text-2xl.font-bold.text-blue-600")).to_be_visible()
        
        # Verify the table headers are present
        # Using XPath for precise text matching
        expect(page.locator('//th[text()="Name"]')).to_be_visible()
        expect(page.locator('//th[text()="Expense Type"]')).to_be_visible()
        expect(page.locator('//th[text()="Type"]')).to_be_visible()
        expect(page.locator('//th[text()="Date Added"]')).to_be_visible()
        expect(page.locator('//th[text()="Actions"]')).to_be_visible()
