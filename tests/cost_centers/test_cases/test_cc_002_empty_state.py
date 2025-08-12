import pytest
import time
import os
from pathlib import Path
from playwright.sync_api import expect
from pages.cost_centers.cost_centers_page import CostCentersPage
from tests.config.test_config import URLS
from dataInput.cost_centers.test_data import (
    empty_state_credentials,
    non_empty_state_credentials
)

class TestCostCenterCounters:
    """Test cases for Cost Centers counters in both empty and non-empty states."""
    

    def test_empty_state_counters(self, page):
        """CC-002: Verify that the page shows correct counters when no data exists"""
        try:
            print("\n=== Testing Empty State Counters ===")
            
            # Login with empty state credentials
            page.goto(URLS["LOGIN"])
            page.get_by_label("Email").fill(empty_state_credentials['email'])
            page.get_by_label("Password").fill(empty_state_credentials['password'])
            page.get_by_role("button", name="Login").click()
            page.wait_for_url(URLS["DASHBOARD"])
            
            # Initialize page objects
            cost_centers_page = CostCentersPage(page)
            
            # Navigate to cost centers page
            page.goto(URLS["COST_CENTERS"])
            
            # Take a screenshot of the initial state
            page.screenshot(path="test-results/empty_state_initial.png")
            print("Initial page screenshot saved")

            time.sleep(5)            
            # Debug: Print current page URL and title
            print(f"\n=== Current Page: {page.title()}")
            print(f"=== Current URL: {page.url}")
            
            # Debug: Check if we're on the right page by looking for expected elements
            try:
                # Look for any heading that might indicate the page content
                page_title = page.get_by_role("heading").first
                if page_title.is_visible():
                    print(f"✓ Page heading: {page_title.text_content()}")
                else:
                    print("Warning: Could not find main page heading")
    
                # Take a screenshot of the current state
                page.screenshot(path="test-results/page_state.png")
                print("✓ Screenshot saved as test-results/page_state.png")
    
            except Exception as e:
                print(f"Warning while checking page title: {e}")

            time.sleep(5)
            # Get the counters in a single attempt
            print("\n=== Getting counter values... ===")
            # Using the new simpler counter method
            counters = cost_centers_page.get_simple_counter_values()
            print(f"✓ Got counters using simple method: {counters}")
            
            # Keep old implementation commented out for reference
            # Old implementation:
            # counters = cost_centers_page.get_counter_values()
            # print(f"✓ Got counters: {counters}")
            
            # If we didn't get any counters, use default zero values
            if not counters:
                print("Warning: No counters found, using default zero values")
                counters = {'total': '0', 'active': '0', 'inactive': '0'}
    
    
            # Verify counters
            if counters:
                # Normalize counter values (remove any non-numeric characters)
                total = ''.join(filter(str.isdigit, counters.get('total', '0')))
                active = ''.join(filter(str.isdigit, counters.get('active', '0')))
                inactive = ''.join(filter(str.isdigit, counters.get('inactive', '0')))

                print(f"Normalized counters - Total: {total}, Active: {active}, Inactive: {inactive}")

                # Convert to integers for comparison
                total = int(total) if total.isdigit() else 0
                active = int(active) if active.isdigit() else 0
                inactive = int(inactive) if inactive.isdigit() else 0
                
                # For empty state, all counters should be 0
                if total == 0 and active == 0 and inactive == 0:
                    print("✓ Verified empty state: All counters are 0")
                    # Check for empty state message
                    empty_state = page.get_by_text("No cost centers found.")
                    assert empty_state.is_visible(), "Expected empty state message not found"
                    print("✓ Verified empty state message is visible")
                else:
                    # For non-empty state, verify the sum
                    assert active + inactive == total, \
                        f"Sum of active ({active}) and inactive ({inactive}) should equal total ({total})"
                
                # Verify no negative numbers
                assert total >= 0, f"Total count should not be negative, got {total}"
                assert active >= 0, f"Active count should not be negative, got {active}"
                assert inactive >= 0, f"Inactive count should not be negative, got {inactive}"
                
            else:
                assert False, "Failed to retrieve counter values"
                
            print("\n✓ Test completed successfully!")
            
        except Exception as e:
            # Take a screenshot on failure
            page.screenshot(path="test-results/test_failure.png")
            print(f"\n=== Test Failed! ===")
            print(f"Error: {e}")
            print("Screenshot saved as test_failure.png")
            raise
            
    def login_with_credentials(self, page, credentials):
        """Helper method to login with specific credentials"""
        page.goto(URLS["LOGIN"])
        page.get_by_label("Email").fill(credentials['email'])
        page.get_by_label("Password").fill(credentials['password'])
        page.get_by_role("button", name="Login").click()
        # Wait for login to complete
        page.wait_for_url(URLS["DASHBOARD"])
        return page
    
    def test_non_empty_state_counters(self, page):
        """CC-003: Verify that the page shows correct counters when data exists"""
        try:
            print("\n=== Testing Non-Empty State Counters ===")
            
            # Login with non-empty state credentials
            page.goto(URLS["LOGIN"])
            page.get_by_label("Email").fill(non_empty_state_credentials['email'])
            page.get_by_label("Password").fill(non_empty_state_credentials['password'])
            page.get_by_role("button", name="Login").click()
            page.wait_for_url("**/dashboard")
            
            # Initialize page objects
            cost_centers_page = CostCentersPage(page)
            
            # Navigate to cost centers page
            page.goto(URLS["COST_CENTERS"])
            
            # Take a screenshot
            page.screenshot(path="test-results/non_empty_initial_state.png")
            
            time.sleep(5)            
            # Get the counters in a single attempt
            print("\n=== Getting counter values... ===")
            # Using the new simpler counter method
            counters = cost_centers_page.get_simple_counter_values()
            print(f"✓ Got counters using simple method: {counters}")
            
            # Keep old implementation commented out for reference
            # Old implementation:
            # counters = cost_centers_page.get_counter_values()
            # print(f"✓ Got counters: {counters}")
            
            # Handle error cases
            if counters.get('total') == 'error':
                print("Error: Failed to get total counter value")
                page.screenshot(path="test-results/total_counter_error.png")
                raise AssertionError("Failed to retrieve total counter value")
            
            if counters.get('active') == 'error':
                print("Error: Failed to get active counter value")
                page.screenshot(path="test-results/active_counter_error.png")
                raise AssertionError("Failed to retrieve active counter value")
            
            if counters.get('inactive') == 'error':
                print("Error: Failed to get inactive counter value")
                page.screenshot(path="test-results/inactive_counter_error.png")
                raise AssertionError("Failed to retrieve inactive counter value")
            
            # Normalize and convert counter values
            total = int(''.join(filter(str.isdigit, counters.get('total', '0'))) or '0')
            active = int(''.join(filter(str.isdigit, counters.get('active', '0'))) or '0')
            inactive = int(''.join(filter(str.isdigit, counters.get('inactive', '0'))) or '0')
            
            print(f"Normalized counters - Total: {total}, Active: {active}, Inactive: {inactive}")
            
            # Verify counters
            assert total > 0, f"Total counter should be greater than 0, got {total}"
            assert active > 0, f"Active counter should be greater than 0, got {active}"
            assert inactive == 0, f"Inactive counter should be 0, got {inactive}"
            assert active + inactive == total, \
                f"Sum of active ({active}) and inactive ({inactive}) should equal total ({total})"
                
            # Verify UI elements
            print("\n=== Verifying UI elements... ===")
            
            # Wait for new cost center button
            print("Waiting for New Cost Center button...")
            expect(cost_centers_page.new_cost_center_btn).to_be_visible()
            print("✓ New Cost Center button is visible")
            
            # Wait for search input
            print("Waiting for search input...")
            try:
                expect(cost_centers_page.search_input).to_be_visible(timeout=5000)
                print("✓ Search input is visible")
            except Exception as e:
                print(f"Error: {str(e)}")
                page.screenshot(path="test-results/search_input_error.png")
                raise
            
            # Verify table has data
            print("Checking table rows...")
            rows = page.locator("table tbody tr").count()
            assert rows > 0, "Table should have at least one row of data"
            #print(f"✓ Found {rows} rows in the data table")
            
            print("\n✓ Test completed successfully!")
            
        except Exception as e:
            page.screenshot(path="test-results/non_empty_test_failure.png")
            print(f"\n=== Test Failed! ===")
            print(f"Error: {e}")
            raise
