import pytest
from playwright.sync_api import Page, expect
from pages.cost_centers.cost_centers_page import CostCentersPage
from tests.config.test_config import URLS
from dataInput.cost_centers.test_data import credentials, refresh_test_data

# Register the custom mark to avoid the warning
def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "cost_centers: mark test as part of cost centers test suite"
    )

@pytest.mark.cost_centers
class TestRefreshButton:
    # Get test data from centralized location
    test_data = refresh_test_data
    credentials = credentials
    
    def test_refresh_button(self, page: Page):
        """CC-005: Verify that the 'Refresh' button reloads the cost centers list"""
        try:
            # Login
            page.goto(URLS["LOGIN"])
            page.get_by_label("Email").fill(self.credentials["email"])
            page.get_by_label("Password").fill(self.credentials["password"])
            page.get_by_role("button", name="Login").click()
            page.wait_for_url(URLS["DASHBOARD"])
            
            # Navigate to cost centers page
            page.goto(URLS["COST_CENTERS"])
            
            # Wait for cost centers page to load using test data selectors
            for selector in self.test_data["expected_elements"]:
                page.wait_for_selector(
                    selector, 
                    state="visible", 
                    timeout=self.test_data["timeouts"]["page_load"]
                )
            
            # Create page object
            cost_centers_page = CostCentersPage(page)
            
            # Click the refresh button
            refresh_button = page.get_by_role("button", name="Refresh")
            refresh_button.wait_for(
                state="visible", 
                timeout=self.test_data["timeouts"]["element_visibility"]
            )
            refresh_button.click()
            
            # Wait for counters to be visible and get their values using the simpler method
            counters = cost_centers_page.get_simple_counter_values()
            
            # Keep old implementation commented out for reference
            # Old implementation:
            # counters = cost_centers_page.get_counter_values()
            
            # Verify counter values are valid integers
            for counter_name, counter_value in counters.items():
                try:
                    counter_int = int(counter_value)
                    assert counter_int >= 0, f"{counter_name} counter should be non-negative"
                except ValueError:
                    raise AssertionError(f"{counter_name} counter should be an integer, got: {counter_value}")
            
            # Verify the page URL
            assert page.url == "https://wize-invoice-dev-front.octaprimetech.com/cost-center", "Page URL should be cost centers page"
            
            # Verify the refresh button is still visible
            refresh_button.wait_for(state="visible", timeout=5000)
            
        except Exception as e:
            print(f"Test failed: {str(e)}")
            # Screenshot functionality has been disabled as per user request
            # page.screenshot(path="test_refresh_failure.png")
            raise
        
        # Verify page is still on the same URL
        expect(page).to_have_url("https://wize-invoice-dev-front.octaprimetech.com/cost-center")
