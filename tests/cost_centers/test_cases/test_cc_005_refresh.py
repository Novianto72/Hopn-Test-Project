import os
import sys
import pytest
from playwright.sync_api import Page, expect

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

# Now import the URLS
from tests.config.test_config import URLS

# Import other modules
from pages.cost_centers.cost_centers_page import CostCentersPage
from dataInput.cost_centers.test_data import credentials, refresh_test_data

# Register the custom mark to avoid the warning
def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "cost_centers: mark test as part of cost centers test suite"
    )

@pytest.mark.cost_centers
class TestRefreshButton:
    # Class variables
    test_data = refresh_test_data
    credentials = credentials
    urls = URLS  # Store URLS as a class variable
    
    def test_refresh_button(self, page: Page):
        """CC-005: Verify that the 'Refresh' button reloads the cost centers list"""
        try:
            # Debug: Print the current working directory and URLS
            print(f"Current working directory: {os.getcwd()}")
            print(f"URLS: {self.urls}")
            
            # Login
            login_url = self.urls["LOGIN"]
            print(f"Navigating to login URL: {login_url}")
            page.goto(login_url)
            
            # Fill in credentials and login
            page.get_by_label("Email").fill(self.credentials["email"])
            page.get_by_label("Password").fill(self.credentials["password"])
            page.get_by_role("button", name="Login").click()
            page.wait_for_url(self.urls["DASHBOARD"])
            
            # Navigate to cost centers page
            cost_centers_url = self.urls["COST_CENTERS"]
            print(f"Navigating to cost centers URL: {cost_centers_url}")
            page.goto(cost_centers_url)
            
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
            from tests.config.test_config import URLS
            assert page.url == URLS["COST_CENTERS"], f"Page URL should be {URLS['COST_CENTERS']}"
            
            # Verify the refresh button is still visible
            refresh_button.wait_for(state="visible", timeout=5000)
            
        except Exception as e:
            print(f"Test failed: {str(e)}")
            # Screenshot functionality has been disabled as per user request
            # page.screenshot(path="test_refresh_failure.png")
            raise
        
        # Verify page is still on the same URL
        from tests.config.test_config import URLS
        expect(page).to_have_url(URLS["COST_CENTERS"])
