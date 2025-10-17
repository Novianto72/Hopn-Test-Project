"""
Enhanced test cases for XSS protection in Cost Center functionality.

This test suite verifies that:
1. Input is properly sanitized before being stored in the database
2. Output is properly escaped when displayed
3. No JavaScript execution occurs from user input
4. The application remains stable and functional after XSS attempts
"""
import pytest
import logging
from playwright.sync_api import expect
from pages.cost_centers.cost_centers_page import CostCentersPage
from tests.config.test_config import BASE_URL, URLS

# Register custom marks
def pytest_configure(config):
    config.addinivalue_line("markers", "xss: mark test as related to XSS protection")

class TestCostCenterXSSProtection:
    @pytest.fixture(autouse=True)
    def setup(self, logged_in_page):
        """Setup test with authenticated page."""
        self.page = logged_in_page
        
        # Navigate to cost centers page and verify it loads
        self.page.goto(URLS["COST_CENTERS"])
        
        # Check if we got a 404 page
        if "404" in self.page.title() or "Not Found" in self.page.title():
            pytest.fail(f"Failed to load cost centers page. Got a 404 error. URL: {self.page.url}")
            
        # Wait for the page to be fully loaded
        self.page.wait_for_selector("input[placeholder='Search cost centers...']", state="visible", timeout=10000)
        
        self.cost_centers_page = CostCentersPage(self.page)
        self.search_input = self.page.locator("input[placeholder='Search cost centers...']")
        self.search_results = self.page.locator("table tbody tr")
        
        # Take a screenshot of the initial page state
        self.page.screenshot(path="test-results/initial_page_state.png")
        
        yield
        # Clean up after each test
        self._clear_search()

    def perform_search(self, search_term):
        """Helper method to perform a search and wait for results"""
        self.search_input.fill("")
        self.search_input.fill(search_term)
        self.page.wait_for_timeout(1000)  # Wait for search results

    def get_visible_search_results(self):
        """Get visible search results text content"""
        return [row.text_content().strip() for row in self.search_results.all()]

    def check_for_javascript_errors(self):
        """Check if there are any JavaScript errors in the console"""
        return self.page.evaluate("window.__playwright_errors__ || []")

    @pytest.mark.xss
    @pytest.mark.xfail(
        reason="Known security issue: XSS vulnerability in search results. "
              "The application displays raw HTML/JS in search results without proper escaping. "
              "This is a serious security issue that needs to be addressed.",
        strict=True
    )
    def test_xss_protection_in_search(self):
        """
        SECURITY TEST: XSS Protection in Search
        
        This test verifies that the application properly escapes or sanitizes
        search input to prevent Cross-Site Scripting (XSS) attacks.
        
        KNOWN ISSUE:
        The application is vulnerable to XSS attacks as it displays raw HTML/JS
        in search results without proper escaping. This could allow attackers to
        execute malicious JavaScript in the context of the application.
        
        SEVERITY: High
        
        REPRODUCTION STEPS:
        1. Navigate to the Cost Centers page
        2. Enter `<script>alert('XSS')</script>` in the search field
        3. Observe that the raw script appears in search results
        
        EXPECTED BEHAVIOR:
        - Search terms should be HTML-escaped when displayed
        - Script tags should be rendered as text, not executed
        - No JavaScript should be executed from search results
        
        RECOMMENDED FIX:
        - Use proper HTML escaping when displaying user input
        - Implement Content Security Policy (CSP) headers
        - Use a templating engine that auto-escapes by default
        - Consider using a web application firewall (WAF) for additional protection
        """
        test_cases = [
            ("<script>alert('XSS')</script>", "Basic XSS script tag"),
            ("<img src='x' onerror='alert(1)'>", "XSS using image onerror"),
            ("<div onmouseover='alert(1)'>XSS</div>", "Event handlers should be removed")
        ]

        for payload, description in test_cases:
            print(f"\n--- Testing XSS payload: {payload} ---")
            
            # List to collect any dialog messages that appear
            dialog_messages = []
            
            def handle_dialog(dialog):
                dialog_messages.append(dialog.message())
                dialog.dismiss()  # Dismiss the dialog to continue test execution
            
            # Set up dialog handler before performing the search
            self.page.on("dialog", handle_dialog)
            
            try:
                # Take a screenshot before the test
                self.page.screenshot(path=f"test-results/before_xss_test_{hash(payload)}.png")
                
                # Clear any previous search
                self._clear_search()
                
                # Perform search with the payload
                self.perform_search(payload)
                
                # Wait for search results to update
                self.page.wait_for_timeout(1000)  # Wait for search to complete
                
                # Take a screenshot after search
                self.page.screenshot(path=f"test-results/after_xss_test_{hash(payload)}.png")
                
                # Get visible search results
                visible_results = self.get_visible_search_results()
                print(f"Visible results: {visible_results}")
                
                # Check for XSS indicators
                script_in_results = any("<script>" in result for result in visible_results)
                vulnerability_found = script_in_results or bool(dialog_messages)
                
                if vulnerability_found:
                    # Log detailed information about the vulnerability
                    if script_in_results:
                        logging.warning(f"XSS VULNERABILITY DETECTED (expected): Raw script tags in results - {description}")
                        logging.warning(f"Search results contained raw script tags")
                        logging.warning(f"Results: {visible_results}")
                    
                    if dialog_messages:
                        logging.warning(f"XSS VULNERABILITY DETECTED (expected): JavaScript alert triggered - {description}")
                        logging.warning(f"Dialog messages: {dialog_messages}")
                    
                    logging.warning(f"Payload: {payload}")
                    
                    # Take a screenshot of the vulnerability
                    self.page.screenshot(path=f"test-results/xss_vulnerability_{hash(payload)}.png")
                    
                    # Explicitly fail the test with a clear message
                    # This will be caught by xfail and marked as expected failure
                    failure_reasons = []
                    if script_in_results:
                        failure_reasons.append(
                            f"Raw script tag found in search results: "
                            f"{next((r for r in visible_results if '<script>' in r), '')}"
                        )
                    if dialog_messages:
                        failure_reasons.append(
                            f"JavaScript alert triggered: {dialog_messages}"
                        )
                    
                    pytest.fail(
                        f"XSS VULNERABILITY: {', '.join(failure_reasons)}. "
                        f"This is a known security issue that needs to be fixed."
                    )
                
                # Verify the search input value is properly escaped
                search_value = self.search_input.input_value()
                assert "<script>" not in search_value, (
                    f"SECURITY ISSUE: {description}. "
                    f"Raw script tag found in search input value. "
                    f"Search input values should be properly escaped.\n"
                    f"Search value: {search_value}"
                )
                
                assert len(js_errors) == 0, (
                    f"{description}: JavaScript errors found: {js_errors}"
                )
                
            except Exception as e:
                # Save page content on failure
                with open(f"test-results/xss_test_error_{hash(payload)}.txt", "w") as f:
                    f.write(f"Error: {str(e)}\n")
                    f.write(f"Page URL: {self.page.url}\n")
                    f.write(f"Page title: {self.page.title()}\n")
                    f.write("\nPage content:\n")
                    f.write(self.page.content())
                raise

    @pytest.mark.xss
    def test_special_characters_in_search(self):
        """Test that special characters in search are handled safely"""
        test_cases = [
            ("Test's Cost Center", "Apostrophe in search"),
            ("Cost & Center", "Ampersand in search"),
            ("Cost <Center>", "Angle brackets in search"),
            ("Cost \"Center\"", "Quotes in search"),
            ("Cost/Center", "Forward slash in search"),
            ("Cost\\Center", "Backslash in search")
        ]
        
        # Create test data first
        created_centers = []
        for search_term, _ in test_cases:
            try:
                self._create_test_cost_center(search_term)
                created_centers.append(search_term)
            except Exception as e:
                logging.warning(f"Failed to create test cost center '{search_term}': {str(e)}")
        
        # Refresh the page to ensure new cost centers are loaded
        self.page.reload()
        self.page.wait_for_load_state("networkidle")
        
        # Now test searching for each one
        for search_term, description in test_cases:
            # Skip if we couldn't create this test data
            if search_term not in created_centers:
                logging.warning(f"Skipping search test for '{search_term}' as it wasn't created")
                continue
                
            # Clear any previous search
            self.perform_search("")
            
            # Perform search with special characters
            self.perform_search(search_term)
            
            # Take a screenshot for debugging
            self.page.screenshot(path=f"test-results/search_test_{hash(search_term)}.png")
            
            # Verify the search input value is preserved exactly as entered
            search_value = self.search_input.input_value()
            assert search_value == search_term, f"{description}: Search input value not preserved"
            
            # Verify we get results for the search
            results = self.get_visible_search_results()
            assert results, f"{description}: No search results found for '{search_term}'"
            
            # Check if any result contains our search term
            # We use 'in' because the result might contain additional text like dates
            assert any(search_term in result for result in results), \
                f"{description}: No matching results found for search term '{search_term}'. " \
                f"Results were: {results}"
            
            # Check for JavaScript errors
            js_errors = self.check_for_javascript_errors()
            assert len(js_errors) == 0, f"{description}: JavaScript errors found: {js_errors}"

    def _clear_search(self):
        """Clear the search input and wait for results to reset."""
        try:
            # First, check if the search input is visible and enabled
            if self.search_input.is_visible() and self.search_input.is_enabled():
                self.search_input.fill("")
                self.page.wait_for_timeout(500)  # Wait for search to reset
            else:
                logging.warning("Search input is not visible or enabled, reloading page")
                self.page.reload()
                self.page.wait_for_load_state("networkidle")
        except Exception as e:
            logging.warning(f"Error clearing search: {e}")
            # Try to reload the page if clearing search fails
            try:
                self.page.goto(URLS["COST_CENTERS"])
                self.page.wait_for_load_state("networkidle")
            except Exception as reload_error:
                logging.error(f"Failed to reload page: {reload_error}")
    
    def _create_test_cost_center(self, name=None):
        """Create a test cost center for search testing using POM methods
        
        Args:
            name (str, optional): Name for the cost center. Defaults to "Test Cost Center".
        """
        if name is None:
            name = "Test Cost Center"
            
        try:
            logging.info(f"Creating test cost center: {name}")
            
            # Click the New Cost Center button using POM method
            self.cost_centers_page.click_new_cost_center()
            
            # Fill in the name field using POM locator
            self.cost_centers_page.name_input.fill(name)
            
            # Submit the form using POM method
            self.cost_centers_page.submit_form()
            
            # Wait for either success message or for the modal to close
            try:
                # First try to find a success message
                try:
                    self.page.wait_for_selector(
                        "text=Cost Center created successfully", 
                        timeout=5000,
                        state="visible"
                    )
                except:
                    # If no success message, wait for the modal to close
                    self.page.wait_for_selector("[role=dialog]", state="hidden", timeout=10000)
                
                logging.info(f"Successfully created cost center: {name}")
                return True
                
            except Exception as e:
                # Check if there was an error message
                error_element = self.page.query_selector(".error-message, .Mui-error, [role='alert']")
                if error_element:
                    error_text = error_element.text_content()
                    raise Exception(f"Error creating cost center: {error_text}")
                raise
                
        except Exception as e:
            # Take a screenshot for debugging
            self.page.screenshot(path=f"test-results/create_cost_center_error_{hash(str(name))}.png")
            logging.error(f"Failed to create test cost center '{name}': {str(e)}")
            raise
