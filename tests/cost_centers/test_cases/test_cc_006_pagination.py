import re
import pytest
from playwright.sync_api import expect, Page
from pages.cost_centers.cost_centers_page import CostCentersPage
from tests.config.test_config import URLS
from dataInput.cost_centers.test_data import (
    credentials,
    empty_state_credentials,
    pagination_test_data
)

class TestPagination:
    """Test cases for Cost Centers pagination functionality."""
    
    # Get test data from centralized location
    test_data = pagination_test_data
    credentials_with_data = credentials
    credentials_no_data = empty_state_credentials
    
    # @pytest.fixture(autouse=True)
    # def setup(self, logged_in_page):
    #     """Default setup with default credentials (with data)."""
    #     # By default, use credentials with data
    #     self.credentials = self.credentials_with_data
    #     self.page = logged_in_page
    #     self.cost_centers_page = CostCentersPage(logged_in_page)
    #     return self
    # 
    # @pytest.fixture
    # def setup_no_data(self, logged_in_page):
    #     """Setup for no-data test."""
    #     # Override credentials for no-data test
    #     self.credentials = self.credentials_no_data
    #     self.page = logged_in_page
    #     self.cost_centers_page = CostCentersPage(logged_in_page)
    #     return self
    
    def login_and_navigate_to_cost_centers(self, page: Page):
        """Helper method to perform login and navigate to Cost Centers page."""
        try:
            # Login with credentials that have data
            page.goto(URLS["LOGIN"])
            page.get_by_label("Email").fill(self.credentials_with_data["email"])
            page.get_by_label("Password").fill(self.credentials_with_data["password"])
            page.get_by_role("button", name="Login").click()
            page.wait_for_url(URLS["DASHBOARD"])
            
            # Navigate to cost centers page
            page.goto(URLS["COST_CENTERS"])
            page.wait_for_selector("h1:has-text('Cost Centers')", state="visible", timeout=10000)
            return CostCentersPage(page)
            
        except Exception as e:
            pytest.fail(f"Failed during login/navigation: {str(e)}")
            
    def verify_pagination_controls(self, pagination_container, expected_pages: int):
        """Verify pagination controls are present and functional."""
        # Wait for pagination controls to be visible
        pagination_container.wait_for(state="visible", timeout=10000)
        
        # Verify page info text
        page_info = pagination_container.locator("div.text-sm.font-medium.text-gray-900:has-text('Page')")
        assert page_info.count() > 0, "Page info text not found"
        
        # Verify navigation buttons
        if expected_pages > 1:
            next_button = pagination_container.locator('button[title="Next page"]')
            assert next_button.count() > 0, "Next button not found"
            
    def test_pagination_with_5_records_per_page(self, page: Page):
        """CC-006-1: Verify pagination with 5 records per page
        
        Test Steps:
        1. Login and navigate to Cost Centers page
        2. Set page size to 5 records
        3. Verify initial pagination state
        4. Verify number of displayed rows
        5. Test pagination controls
        """
        # Take screenshot on failure
        try:
            # Login and navigate to Cost Centers page
            cost_centers_page = self.login_and_navigate_to_cost_centers(page)
            
            # Set page size to 5 records per page and verify
            items_per_page = 5
            cost_centers_page.set_page_size(items_per_page)
            
            # Verify table is loaded
            table = page.locator("table")
            table.wait_for(state="visible", timeout=10000)
            
            # Get total number of cost centers
            counters = cost_centers_page.get_simple_counter_values()
            total_centers = int(counters['total'])
            
            # Calculate expected number of pages
            expected_pages = (total_centers + items_per_page - 1) // items_per_page
            print(f"Total cost centers: {total_centers}, Expected pages: {expected_pages}")
            
            # Get pagination container
            pagination_container = page.locator("div.bg-gray-50.px-3.py-4.border-t.border-gray-200")
            
            # Verify initial pagination state
            self.verify_pagination_controls(pagination_container, expected_pages)
            
            # Get page info
            page_info = pagination_container.locator("div.text-sm.font-medium.text-gray-900:has-text('Page')").first
            page_info_text = page_info.inner_text()
            print(f"Page info text: {page_info_text}")
            
            # Parse and verify page info
            match = re.match(r'Page (\d+) of (\d+)', page_info_text)
            assert match, f"Could not parse page info: {page_info_text}"
            
            current_page = int(match.group(1))
            total_pages = int(match.group(2))
            
            # Verify initial page state
            assert current_page == 1, f"Should start on page 1, but got page {current_page}"
            assert total_pages == expected_pages, \
                f"Expected {expected_pages} total pages, but got {total_pages}"
            
            # Verify number of rows matches expected items per page
            rows = page.locator("table tbody tr")
            actual_row_count = rows.count()
            expected_row_count = min(items_per_page, total_centers)
            assert actual_row_count == expected_row_count, \
                f"Expected {expected_row_count} rows, but found {actual_row_count}"
            
            # Store pagination info for reference
            pagination_info = {
                'current_page': current_page,
                'total_pages': total_pages,
                'items_per_page': items_per_page,
                'total_items': total_centers
            }
            print(f"Pagination info: {pagination_info}")
            # Test pagination navigation if there are multiple pages
            #if expected_pages > 1:
            #    self.test_pagination_navigation(page, pagination_container, total_centers, items_per_page)
                
        except Exception as e:
            # Take screenshot on failure
            screenshot = page.screenshot(full_page=True)
            print(f"Test failed with error: {str(e)}")
            print(f"Page URL: {page.url}")
            print("Screenshot taken")
            raise
                
    def wait_and_click_button(self, page: Page, button_locator, button_name="button"):
        """Helper method to wait for button to be ready and click it.
        
        Args:
            page: Playwright Page object
            button_locator: Locator for the button to click
            button_name: Name of the button for logging purposes
        """
        try:
            print(f"Waiting for {button_name} button to be visible and enabled...")
            # Wait for button to be visible and enabled
            button_locator.wait_for(state="visible", timeout=10000)
            button_locator.wait_for(state="enabled", timeout=10000)
            
            # Scroll the button into view
            print("Scrolling button into view...")
            button_locator.scroll_into_view_if_needed()
            
            # Add a small delay to ensure everything is stable
            print("Waiting for UI to stabilize...")
            page.wait_for_timeout(1000)
            
            # Click the button
            print(f"Clicking {button_name} button...")
            button_locator.click()
            
            # Wait for any resulting navigation/updates
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(1000)  # Additional wait for UI updates
            
        except Exception as e:
            # Take screenshot for debugging
            screenshot = page.screenshot(full_page=True)
            print(f"Failed to click {button_name}. Screenshot taken.")
            print(f"Button state - visible: {button_locator.is_visible()}, enabled: {button_locator.is_enabled()}")
            raise Exception(f"Failed to click {button_name}: {str(e)}")

    def test_pagination_navigation(self, page: Page, pagination_container, total_items: int, items_per_page: int):
        """Test pagination navigation functionality.
        
        Args:
            page: Playwright Page object
            pagination_container: Locator for the pagination container
            total_items: Total number of items
            items_per_page: Number of items per page
        """
        try:
            # Get navigation buttons - using index 1 as there are multiple matches
            next_button = page.locator('//button[@title="Next page"]').nth(1)
            prev_button = page.locator('//button[@title="Previous page"]').nth(1)
            
            print("Waiting for pagination controls to be ready...")
            
            # Wait for pagination container to be stable
            pagination_container.wait_for(state="visible", timeout=10000)
            
            # Verify initial button states
            prev_button.wait_for(state="visible", timeout=10000)
            next_button.wait_for(state="visible", timeout=10000)
            
            # Verify initial state
            assert not prev_button.is_enabled(), "Previous button should be disabled on first page"
            assert next_button.is_enabled(), "Next button should be enabled"
            
            # Navigate to next page with better waiting
            print("Attempting to click Next button...")
            self.wait_and_click_button(page, next_button, "Next page")
            
            # Wait for page to update and verify
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(1000)  # Additional wait for UI updates
            
            # Verify page updated to page 2
            current_page_info = pagination_container.locator("div.text-sm.font-medium.text-gray-900:has-text('Page')").first
            current_page_info.wait_for(state="visible", timeout=10000)
            
            page_info_text = current_page_info.inner_text()
            print(f"Current page info after clicking Next: {page_info_text}")
            
            match = re.match(r'Page (\d+) of (\d+)', page_info_text)
            assert match, f"Could not parse page info: {page_info_text}"
            
            current_page = int(match.group(1))
            assert current_page == 2, f"Should be on page 2 after clicking Next, but got page {current_page}"
            
            # Verify previous button is now enabled
            prev_button.wait_for(state="enabled", timeout=5000)
            assert prev_button.is_enabled(), "Previous button should be enabled after navigation"
            
            # Navigate back to first page with better waiting
            print("Attempting to click Previous button...")
            self.wait_and_click_button(page, prev_button, "Previous page")
            
            # Verify back on first page
            page.wait_for_load_state("networkidle")
            current_page_info = pagination_container.locator("div.text-sm.font-medium.text-gray-900:has-text('Page')").first
            current_page_info.wait_for(state="visible", timeout=10000)
            
            page_info_text = current_page_info.inner_text()
            print(f"Current page info after clicking Previous: {page_info_text}")
            
            match = re.match(r'Page (\d+) of (\d+)', page_info_text)
            assert match, f"Could not parse page info: {page_info_text}"
            
            current_page = int(match.group(1))
            assert current_page == 1, f"Should be back on page 1 after clicking Previous, but got page {current_page}"
                
        except Exception as e:
            # Take screenshot on failure
            screenshot = page.screenshot(full_page=True)
            print(f"Test failed with error: {str(e)}")
            print(f"Page URL: {page.url}")
            print("Screenshot taken")
            raise
    
    def test_pagination_with_no_data(self, page: Page):
        """CC-006: Verify pagination control is present and disabled when no data"""
        try:
            # Login with credentials that have no data
            page.goto(URLS["LOGIN"])
            page.get_by_label("Email").fill(self.credentials_no_data["email"])
            page.get_by_label("Password").fill(self.credentials_no_data["password"])
            page.get_by_role("button", name="Login").click()
            page.wait_for_url(URLS["DASHBOARD"])
            
            # Navigate to cost centers page
            page.goto(URLS["COST_CENTERS"])
            
            # Wait for page to load and verify we're on the right page
            page.wait_for_selector("h1:has-text('Cost Centers')")
            
            # Create page object
            cost_centers_page = CostCentersPage(page)
            
            # Get pagination info
            pagination = cost_centers_page.get_pagination_info()
            print(f"Pagination info: {pagination}")
            
            # Verify pagination shows 1 of 1
            assert pagination['current'] == 1, "Current page should be 1"
            assert pagination['total'] == 1, f"Total pages should be 1 when no data, got {pagination['total']}"
            
            # Check for pagination controls
            pagination_container = page.locator(".pagination").first
            if pagination_container.is_visible():
                # If pagination is visible, check the buttons
                prev_button = pagination_container.locator("button:has-text('Previous')")
                next_button = pagination_container.locator("button:has-text('Next')")
                
                if prev_button.is_visible():
                    assert prev_button.is_disabled(), "Previous button should be disabled on first page"
                if next_button.is_visible():
                    assert next_button.is_disabled(), "Next button should be disabled on last page"
            else:
                print("Pagination container not visible, assuming single page with no data")
            # Get pagination info
            pagination = cost_centers_page.get_pagination_info()
            print(f"Pagination info: {pagination}")
            
            # Verify pagination shows 1 of 1
            assert pagination['current'] == 1, "Current page should be 1"
            assert pagination['total'] == 1, f"Total pages should be 1 when no data, got {pagination['total']}"
            
            # Check for pagination controls
            pagination_container = page.locator(".pagination").first
            if pagination_container.is_visible():
                # If pagination is visible, check the buttons
                prev_button = pagination_container.locator("button:has-text('Previous')")
                next_button = pagination_container.locator("button:has-text('Next')")
                
                if prev_button.is_visible():
                    assert prev_button.is_disabled(), "Previous button should be disabled on first page"
                if next_button.is_visible():
                    assert next_button.is_disabled(), "Next button should be disabled on last page"
            else:
                print("Pagination container not visible, assuming single page with no data")
                
        except Exception as e:
            print(f"Test failed: {str(e)}")
            # Screenshot functionality has been disabled as per user request
            # page.screenshot(path="test_pagination_no_data_failure.png")
            raise
