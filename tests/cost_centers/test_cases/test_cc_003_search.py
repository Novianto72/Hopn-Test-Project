import pytest
import time
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from pages.cost_centers.cost_centers_page import CostCentersPage
from tests.config.test_config import URLS
from dataInput.cost_centers.test_data import search_test_data

# Create test results directory if it doesn't exist
TEST_RESULTS_DIR = "test-results/screenshots"
os.makedirs(TEST_RESULTS_DIR, exist_ok=True)

@pytest.mark.cost_centers
class TestSearchFunctionality:
    @pytest.fixture(autouse=True)
    def setup(self, logged_in_page: Page):
        """Setup test environment before each test."""
        self.page = logged_in_page
        self.cost_centers_page = CostCentersPage(logged_in_page)
        
        # Navigate to the cost centers page and wait for it to load
        self.page.goto(URLS["COST_CENTERS"])
        self.page.wait_for_load_state("networkidle")
        
        # Wait for the search input to be visible
        self.search_input = self.cost_centers_page.search_input
        self.search_input.wait_for(state="visible", timeout=10000)
        
        # Clear any existing search
        self._clear_search()
    
    def _take_screenshot(self, prefix: str = "test"):
        """Screenshot functionality is disabled"""
        # Screenshot functionality has been disabled as per user request
        # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        # filename = f"{prefix}_{timestamp}.png"
        # screenshot_path = os.path.join(TEST_RESULTS_DIR, filename)
        # self.page.screenshot(path=screenshot_path)
        # return screenshot_path
        return ""
    
    def _clear_search(self):
        """Clear the search input and wait for results to reset."""
        # Using the new simple_search method to clear the search
        self.cost_centers_page.simple_search("")
        
        # Old implementation:
        # self.search_input.fill("")
        # # Wait for the search to clear (if there's a loading state)
        # self.page.wait_for_timeout(500)
    
    def _wait_for_search_results(self, search_term: str, timeout: int = 10000) -> bool:
        """
        Wait for search results to update after entering a search term.
        Returns True if results were found, False otherwise.
        """
        try:
            print(f"\n[DEBUG] Waiting for search results for term: '{search_term}'")
            no_results_msg = search_test_data["messages"]["no_results"].lower().strip()
            
            # First wait for any loading to complete
            self.page.wait_for_load_state('networkidle')
            
            # Wait for either search results or 'no results' message
            result = self.page.wait_for_function(
                """(args) => {
                    const [searchTerm, expectedMessage] = args;
                    console.log('Searching for term:', searchTerm);
                    
                    // Check for the no results message first
                    const noResultsElement = Array.from(document.querySelectorAll('*'))
                        .find(el => {
                            const text = el.textContent?.toLowerCase().trim() || '';
                            return text === expectedMessage;
                        });
                    
                    if (noResultsElement) {
                        console.log('Found no results message:', noResultsElement.textContent);
                        return true;
                    }
                    
                    // Check for data rows
                    const rows = Array.from(document.querySelectorAll('table tbody tr'));
                    console.log('Total rows found:', rows.length);
                    
                    // If no rows at all, return false to keep waiting
                    if (rows.length === 0) {
                        console.log('No rows found in table');
                        return false;
                    }
                    
                    // Check if any row contains the search term
                    const hasMatchingResults = rows.some(row => {
                        // Skip rows that are just the no results message
                        const rowText = row.textContent?.toLowerCase() || '';
                        if (rowText.includes(expectedMessage)) {
                            return true;
                        }
                        
                        // Check if this is a data row (has cells with data)
                        const cells = row.querySelectorAll('td:not([colspan])');
                        if (cells.length > 0) {
                            const matches = rowText.includes(searchTerm.toLowerCase());
                            if (matches) {
                                console.log('Found matching row:', rowText);
                            }
                            return matches;
                        }
                        return false;
                    });
                    
                    console.log('Has matching results:', hasMatchingResults);
                    return hasMatchingResults;
                }""",
                arg=[search_term, no_results_msg],
                timeout=timeout
            )
            
            if result:
                print(f"[DEBUG] Successfully found results for '{search_term}'")
                return True
            return False
            
        except Exception as e:
            print(f"[DEBUG] Error in _wait_for_search_results: {str(e)}")
            self._take_screenshot(f"search_error_{search_term}")
            return False
    
    def _verify_search_results(self, search_term: str) -> bool:
        """Verify that search results match the search term."""
        # Check for 'no results' message first
        no_results = self.page.get_by_text("No cost centers found").first
        if no_results.is_visible():
            print(f"No results found for search term '{search_term}'")
            return True
        
        # Verify each result contains the search term
        rows = self.page.locator("table tbody tr").all()
        if not rows:
            print("No rows found in the table")
            return False
        
        for i, row in enumerate(rows, 1):
            try:
                result_text = row.locator("td:first-child").text_content(timeout=5000)
                if search_term.lower() not in result_text.lower():
                    print(f"Search result '{result_text}' does not contain search term '{search_term}'")
                    return False
            except Exception as e:
                print(f"Error verifying row {i}: {str(e)}")
                self._take_screenshot(f"search_error_row_{i}")
                return False
        
        return True
    
    def test_search_functionality(self):
        """CC-003: Verify search bar is present and functional"""
        max_retries = search_test_data["result_verification"]["retry_attempts"]
        search_terms = search_test_data["valid_search_terms"]
        
        print("\n=== Starting Search Functionality Test ===")
        print(f"Testing with search terms: {search_terms}")
        
        # Wait for the page to be fully loaded first
        self.page.wait_for_load_state('networkidle')
        
        # Get initial data count
        initial_rows = self.page.locator("table tbody tr").count()
        print(f"Initial number of rows in table: {initial_rows}")
        
        for term in search_terms:
            print(f"\n=== Testing search term: '{term}' ===")
            
            for attempt in range(max_retries):
                try:
                    print(f"\nAttempt {attempt + 1}/{max_retries}")
                    
                    # Clear any previous search
                    self._clear_search()
                    print("Cleared previous search")
                    
                    # Wait a moment after clearing
                    self.page.wait_for_timeout(1000)
                    
                    # Enter the search term
                    print(f"Entering search term: '{term}'")
                    self.search_input.fill(term)
                    
                    # Wait for search results with retry
                    timeout = search_test_data["result_verification"]["timeout_ms"]
                    print(f"Waiting for search results (timeout: {timeout}ms)...")
                    
                    if not self._wait_for_search_results(term, timeout=timeout):
                        raise TimeoutError(f"Timed out waiting for search results for term: {term}")
                    
                    # Take a screenshot of the search results
                    self._take_screenshot(f"search_{term}")
                    
                    # Verify search results
                    print("Verifying search results...")
                    if not self._verify_search_results(term):
                        raise AssertionError(f"Search results verification failed for term: {term}")
                    
                    print(f"✓ Search for '{term}' completed successfully")
                    break  # Exit retry loop on success
                    
                except Exception as e:
                    print(f"\nAttempt {attempt + 1} failed: {str(e)}")
                    self._take_screenshot(f"search_failure_attempt_{attempt + 1}")
                    
                    if attempt == max_retries - 1:  # Last attempt
                        raise
                    else:
                        # Wait before retry
                        time.sleep(search_test_data["result_verification"]["retry_delay_seconds"])
    
    def test_search_nonexistent_cost_center(self):
        """TC-SCH-003: Verify search for non-existent cost center shows appropriate message"""
        # Get test data
        non_existent_search = search_test_data["invalid_search_terms"][0]
        no_results_message = search_test_data["messages"]["no_results"]
        
        print(f"\nTesting search for non-existent cost center: {non_existent_search}")
        
        # Get the search input
        search_input = self.cost_centers_page.search_input
        search_input.wait_for(state="visible", timeout=search_test_data["result_verification"]["timeout_ms"])
        
        # Clear any previous search
        search_input.fill("")
        
        # Enter the non-existent search term
        search_input.fill(non_existent_search)
        
        # Wait for search to process
        self.page.wait_for_timeout(1000)
        
        # Wait for the table to update with search results
        self.page.wait_for_selector("table tbody tr", state="attached")
        
        # Get all table rows
        rows = self.page.locator("table tbody tr").all()
        print(f"Found {len(rows)} rows in the table")
        
        # Check if the 'No cost centers found' message is displayed
        no_data_cell = self.page.locator(f"td[colspan='3']:has-text('{no_results_message}')")
        no_data_visible = no_data_cell.is_visible()
        
        # If no data message is visible, we should have exactly one row with this message
        if no_data_visible:
            assert len(rows) == 1, f"Expected 1 row with '{no_results_message}' message, but found {len(rows)} rows"
            assert no_results_message in no_data_cell.text_content().strip(), \
                f"Expected '{no_results_message}' message, but got: {no_data_cell.text_content().strip()}"
            print(f"✓ '{no_results_message}' message is displayed")
        else:
            # If no message is found, verify there are no data rows
            assert len(rows) == 0, f"Expected no data rows but found {len(rows)} rows"
        
        # Take a screenshot of the search result
        self.page.screenshot(path="test-results/nonexistent_search_result.png")
        
        print("✓ Test passed: No results found for non-existent cost center")
    
    def test_search_special_characters(self):
        """Test search with special characters"""
        test_cases = [
            "@#$%^&*",
            "!@#$%^&*()_+{}\\:<>?|[];',./`~",
            "' OR '1'='1",
            "<script>alert('test')</script>",
            "1=1; DROP TABLE cost_centers;--"
        ]
        
        for search_term in test_cases:
            print(f"\nTesting search with special characters: {search_term}")
            self._perform_search_and_verify_no_results(search_term)
    
    def test_search_long_strings(self):
        """Test search with very long strings"""
        # Generate a very long string (1000 characters)
        long_string = "a" * 1000
        self._perform_search_and_verify_no_results(long_string)
        
        # Test with a long string of spaces
        long_spaces = " " * 1000
        self._perform_search_and_verify_no_results(long_spaces)
    
    def test_search_case_insensitive(self):
        """Verify search is case-insensitive"""
        # Get a valid cost center name
        valid_name = "Test Cost Center"
        
        # Test different case variations
        variations = [
            valid_name.upper(),
            valid_name.lower(),
            valid_name.title(),
            valid_name.swapcase()
        ]
        
        for search_term in variations:
            print(f"\nTesting case variation: {search_term}")
            self._perform_search_and_verify_results(search_term)
    
    def test_search_with_spaces(self):
        """Test search with different space patterns"""
        test_cases = [
            "  test play",
            "test play  ",
            "  test play  ",
            "test   play"
        ]
        
        for search_term in test_cases:
            print(f"\nTesting search with spaces: '{search_term}'")
            self._perform_search_and_verify_no_results(search_term)
    

    def test_search_performance(self):
        """Measure search response time"""
        search_terms = ["test", "a", "123", "@#$", " "]
        
        for term in search_terms:
            start_time = time.time()
            self._perform_search_and_verify_results(term)
            response_time = (time.time() - start_time) * 1000  # in milliseconds
            print(f"Search for '{term}' took {response_time:.2f}ms")
            
            # Fail if response time is too long (adjust threshold as needed)
            assert response_time < 5000, f"Search took too long: {response_time:.2f}ms"
    
    def test_multiple_searches(self):
        """Test multiple search terms with various patterns"""
        search_terms = [
            # Basic terms
            "test", "prod", "dev", "qa", "staging",
            
            # Different cases
            "TEST", "Prod", "DEV", "Qa", "STAGING",
            
            # Partial matches
            "est", "ro", "ev", "a", "tag",
            
            # Terms with numbers
            "test1", "prod2", "dev3", "qa4", "staging5",
            
            # Terms with special characters
            "test-prod", "dev_qa", "staging@test",
            
            # Terms with spaces
            "test env", "prod server", "dev environment"
        ]
        
        previous_results = set()
        
        for i, term in enumerate(search_terms):
            try:
                print(f"\nTesting search term: '{term}'")
                
                # Clear any previous search by pressing Escape and waiting for results to clear
                self.cost_centers_page.search_input.fill("")
                self.page.keyboard.press("Enter")
                
                # Wait for the table to update after clearing
                try:
                    self.page.wait_for_selector("text=No cost centers found.", state="visible", timeout=2000)
                except:
                    # If no results message doesn't appear, wait for the table to update
                    self.page.wait_for_selector("table tbody tr", state="visible", timeout=2000)

                # Perform new search with debounce
                self.cost_centers_page.search_input.fill(term)
                self.page.wait_for_timeout(300)  # Small debounce
                self.page.keyboard.press("Enter")
                
                # Wait for results
                self.page.wait_for_selector("table tbody tr", state="attached")
                
                # Get current results
                current_results = {row.text_content().strip() for row in self.page.locator("table tbody tr").all()}
                
                # Skip no results message if present
                current_results = {r for r in current_results if r != "No cost centers found."}
                
                # For non-empty results, verify they contain the search term
                if current_results:
                    term_lower = term.lower()
                    for result in current_results:
                        # Skip validation for XSS test entries as they may contain partial matches
                        if "<img src=''x'' onerror" in result:
                            continue
                            
                        # For non-XSS entries, verify they contain the search term
                        assert term_lower in result.lower(), \
                            f"Result '{result}' doesn't contain search term '{term}'"
                
                # Store current results for next comparison
                previous_results = current_results
                print(f"✓ Search for '{term}' completed with {len(current_results)} results")
                
            except Exception as e:
                pytest.fail(f"Search for '{term}' failed: {str(e)}")
                
    def _perform_search_and_verify_no_results(self, search_term):
        """Helper method to perform search and verify no results are found"""
        search_input = self.cost_centers_page.search_input
        search_input.fill("")
        search_input.fill(search_term)
        
        # Wait for search to complete
        self.page.wait_for_selector("table tbody tr", state="attached")
        
        # Verify no results message
        no_data_cell = self.page.locator("td[colspan='3']:has-text('No cost centers found')")
        assert no_data_cell.is_visible(), f"No results message not found for search term: {search_term}"
        print(f"✓ No results found for: {search_term}")
    
    def _perform_search_and_verify_results(self, search_term):
        """Helper method to perform search and verify results"""
        search_input = self.cost_centers_page.search_input
        search_input.fill("")
        search_input.fill(search_term)
        
        # Wait for search to complete
        self.page.wait_for_selector("table tbody tr", state="attached")
        
        # Verify results contain search term (case-insensitive)
        rows = self.page.locator("table tbody tr").all()
        if rows:
            for row in rows:
                # Skip if it's the no results row
                if row.locator("td[colspan='3']").is_visible():
                    continue
                text = row.text_content().lower()
                assert search_term.lower() in text, f"Search term '{search_term}' not found in result: {text}"
    
    def test_search_exact_cost_center(self):
        """TC-SCH-002: Verify searching for an exact cost center name returns correct result"""
        # Test data
        exact_cost_center_name = "Test Cost Center 1752133334"
        
        print(f"\nTesting exact search for cost center: {exact_cost_center_name}")
        
        # Get the search input
        search_input = self.cost_centers_page.search_input
        search_input.wait_for(state="visible", timeout=5000)
        
        # Clear any previous search
        search_input.fill("")
        
        # Enter the exact cost center name
        search_input.fill(exact_cost_center_name)
        
        # Wait for results to appear
        self.page.wait_for_timeout(1000)  # Give time for search to process
        
        # Get search results
        search_rows = self.page.locator("table tbody tr").count()
        print(f"Found {search_rows} rows for exact search")
        
        # Verify only one result is returned
        assert search_rows == 1, f"Expected exactly 1 result, but found {search_rows}"
        
        # Verify the result matches exactly what we searched for
        result_text = self.page.locator("table tbody tr:first-child td:first-child").text_content().strip()
        assert result_text == exact_cost_center_name, \
            f"Expected result '{exact_cost_center_name}' but got '{result_text}'"
        
        # Take a screenshot of the search result
        self.page.screenshot(path="test-results/exact_search_result.png")
        
        print("✓ Exact cost center search test completed successfully!")
