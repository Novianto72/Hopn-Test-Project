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
    
    def test_pagination_with_5_records_per_page(self, page: Page):
        """CC-006-1: Verify pagination with 5 records per page"""
        try:
            # Login with credentials that have data
            page.goto(URLS["LOGIN"])
            page.get_by_label("Email").fill(self.credentials_with_data["email"])
            page.get_by_label("Password").fill(self.credentials_with_data["password"])
            page.get_by_role("button", name="Login").click()
            page.wait_for_url(URLS["DASHBOARD"])
            
            # Navigate to cost centers page
            page.goto(URLS["COST_CENTERS"])
            
            # Wait for the page to load completely
            page.wait_for_selector("h1:has-text('Cost Centers')", state="visible", timeout=10000)
            
            # Wait for the table to be visible and have data
            try:
                # Wait for the table to be present and visible
                table = page.locator("table")
                table.wait_for(state="visible", timeout=10000)
                
                # Wait for at least one row to be present in the table
                page.wait_for_selector("table tbody tr", state="visible", timeout=10000)
                
                # Verify we have data in the table
                rows = page.locator("table tbody tr").count()
                if rows == 0:
                    pytest.fail("Table is present but contains no rows")
                
                print(f"Found {rows} rows in the cost centers table")
                
                # Get the pagination container with a more specific selector
                try:
                    pagination_container = page.locator(self.test_data["selectors"]["pagination_container"])
                    
                    # Check if we should expect pagination based on row count
                    if rows > 5:
                        # If we have more than 5 rows, pagination should be visible
                        if not pagination_container.is_visible():
                            # Take a screenshot to help with debugging
                            page.screenshot(path="pagination_not_visible.png")
                            print("Pagination container HTML:", pagination_container.inner_html())
                            pytest.fail(f"Pagination should be visible with {rows} rows but wasn't found")
                        else:
                            print("Pagination container is visible as expected")
                    else:
                        # For 5 or fewer rows, pagination might be hidden
                        if pagination_container.is_visible():
                            print("Info: Pagination is visible with few rows")
                        else:
                            print("Info: Pagination not shown as expected with current row count")
                            pytest.skip("Not enough rows to test pagination functionality")
                            
                except Exception as e:
                    page.screenshot(path="pagination_error.png")
                    pytest.fail(f"Error checking pagination container: {str(e)}")
                
            except Exception as e:
                # Take a screenshot for debugging
                page.screenshot(path="debug_pagination_error.png")
                pytest.fail(f"Failed to verify cost centers table: {str(e)}")
            
            # If we get here, we have a valid table with data
            # Now we can proceed with pagination testing
            try:
                # Get pagination elements
                pagination_container = page.locator(self.test_data["selectors"]["pagination_container"])
                rows_per_page_selector = page.locator(self.test_data["selectors"]["rows_per_page_selector"])
                page_info = page.locator(self.test_data["selectors"]["current_page_info"])
                
                # Check if pagination controls are visible
                if not pagination_container.is_visible():
                    print("Pagination container not found. Checking if we have enough rows...")
                    if rows > 5:  # If we have more than 5 rows, pagination should be visible
                        pytest.fail(f"Expected pagination with {rows} rows, but pagination container not found")
                    else:
                        print(f"Only {rows} rows found, pagination not expected")
                        return  # Exit the test as there's no pagination to test
                
                print("Pagination controls found, verifying components...")
                
                # Verify pagination components
                if not rows_per_page_selector.is_visible():
                    print("Warning: Rows per page selector not found")
                
                if not page_info.is_visible():
                    print("Warning: Page info text not found")
                
                # Get the current page info text (e.g., "Page 1 of 8")
                page_info_text = page_info.inner_text()
                print(f"Current page info: {page_info_text}")
                
                # Example: Verify we can change rows per page
                try:
                    rows_per_page_selector.select_option("10")
                    page.wait_for_load_state("networkidle")
                    print("Successfully changed rows per page to 10")
                except Exception as e:
                    print(f"Warning: Could not change rows per page: {str(e)}")
                
            except Exception as e:
                # If we can't determine the state, fail the test
                print(f"Error checking pagination state: {str(e)}")
                raise
            
            # Set page size to 5
            cost_centers_page = CostCentersPage(page)
            cost_centers_page.set_page_size(5)
            
            # Get total number of cost centers using the simpler counter method
            counters = cost_centers_page.get_simple_counter_values()
            total_centers = int(counters['total'])
            
            # Keep old implementation commented out for reference
            # Old implementation:
            # counters = cost_centers_page.get_counter_values()
            # total_centers = int(counters['total'])
            
            # Calculate expected number of pages
            expected_pages = (total_centers + 4) // 5  # Ceiling division
            print(f"Total cost centers: {total_centers}")
            print(f"Expected pages: {expected_pages}")
            
            # Add a small delay to ensure the page size change is fully processed
            page.wait_for_timeout(1000)
            
            # Get current pagination info with debug
            try:
                pagination = cost_centers_page.get_pagination_info()
                print(f"Actual pagination info from UI: {pagination}")
                print(f"Page element text: {cost_centers_page.page.evaluate('document.querySelector("div.text-sm.font-medium.text-gray-900").textContent')}")
            except Exception as e:
                print(f"Error getting pagination info: {str(e)}")
                # Screenshot functionality has been disabled as per user request
                # print("Taking screenshot of pagination area...")
                # page.screenshot(path="pagination_debug.png", full_page=True)
                raise
            
            # Verify pagination shows correct number of pages
            assert pagination['current'] == 1, "Should start on page 1"
            assert pagination['total'] == expected_pages, f"Expected {expected_pages} pages, got {pagination['total']}"
            
            # Verify pagination shows correct number of pages
            assert pagination['current'] == 1, "Should start on page 1"
            assert pagination['total'] == expected_pages, f"Expected {expected_pages} pages, got {pagination['total']}"
            
            print(f"Total cost centers: {total_centers}")
            print(f"Expected pages: {expected_pages}")
            print(f"Actual pages: {pagination['total']}")
            
        except Exception as e:
            print(f"Test failed: {str(e)}")
            # Screenshot functionality has been disabled as per user request
            # page.screenshot(path="test_pagination_5_records_failure.png")
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
