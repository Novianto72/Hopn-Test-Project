"""Test cases for XSS protection in Cost Center search functionality."""
import pytest
from playwright.sync_api import expect
from pages.cost_centers.cost_centers_page import CostCentersPage

class TestCostCenterXSSSearch:
    """Test cases for XSS protection in Cost Center search."""
    
    @pytest.fixture(autouse=True)
    def setup(self, logged_in_page):
        self.page = logged_in_page
        self.cost_centers_page = CostCentersPage(self.page)
        # Navigate to cost centers page
        self.cost_centers_page.navigate()
        
    def test_xss_in_search_field(self):
        """
        CC-012: Verify that XSS attempts in the search field are properly handled.
        """
        # Set up detection variables in the page context
        self.page.evaluate("""() => {
            window.xssDetected = false;
            window.originalAlert = window.alert;
            window.alert = function() {
                window.xssDetected = true;
                console.log('XSS Alert detected');
                return true;
            };
            
            // Add error event listener to catch XSS attempts
            window.addEventListener('error', function(e) {
                if (e.message && e.message.includes('XSS')) {
                    window.xssDetected = true;
                    console.log('XSS Error detected:', e.message);
                }
                return false;
            }, true);
        }""")
        
        # List of XSS payloads to test with descriptions
        xss_test_cases = [
            {"payload": "<script>alert('XSS')</script>", "description": "Basic script tag"},
            {"payload": "<img src='x' onerror='alert(1)'>", "description": "Image with onerror"},
            {"payload": "<svg onload='alert(1)'>", "description": "SVG with onload"},
            {"payload": "javascript:alert('XSS')", "description": "JavaScript URI"},
            {"payload": "Test' OR '1'='1", "description": "SQL injection attempt"},
            {"payload": '" OR "1"="1', "description": "SQL injection with double quotes"},
            {"payload": "'; DROP TABLE cost_centers;--", "description": "SQL injection drop table"}
        ]
        
        for test_case in xss_test_cases:
            payload = test_case["payload"]
            description = test_case["description"]
            print(f"\nTesting XSS: {description}")
            print(f"Payload: {payload}")
            
            try:
                # Reset XSS detection flag
                self.page.evaluate("window.xssDetected = false;")
                
                # Clear any existing search
                search_input = self.page.get_by_placeholder("Search cost centers...")
                search_input.fill("")
                
                # Enter the XSS payload in search (automatic search)
                search_input.fill(payload)
                
                # Wait for debounce and search to complete
                self.page.wait_for_timeout(500)  # Adjust timing as needed
                self.page.wait_for_load_state("networkidle")
                
                # Verify search input value wasn't modified
                search_display = search_input.input_value()
                assert search_display == payload, "Search input value was modified"
                
                # Check if XSS was detected
                xss_detected = self.page.evaluate("window.xssDetected === true;")
                assert not xss_detected, f"XSS detected with payload: {payload}"
                
                # Check if the page is still functional
                assert self.page.title(), "Page title is missing - possible XSS breakage"
                
                # Check for JavaScript errors
                console_errors = []
                self.page.on("console", 
                    lambda msg: console_errors.append(msg) if msg.type == "error" else None
                )
                
                # Get the page content
                page_content = self.page.content().lower()
                
                # Get the page content for analysis
                search_results = self.page.locator("body").inner_html()
                visible_text = self.page.locator("body").inner_text()
                
                # Debug: Print the first 1000 characters of the search results
                print("\n=== Search Results Content ===")
                print(search_results[:1000] + ("..." if len(search_results) > 1000 else ""))
                print("=" * 80)
                
                # Check for unescaped HTML in the visible text (actual security issue)
                dangerous_tags = ["<script>", "<img", "<svg", "onerror=", "onload="]
                if any(tag in visible_text.lower() for tag in dangerous_tags):
                    assert False, f"Unescaped HTML tags found in visible text with payload: {payload}"
                
                # Check if the search term is reflected in the page
                if payload in search_results:
                    # Check if it's properly escaped OR only appears in the input field value
                    input_field = self.page.locator('input[placeholder="Search cost centers..."]')
                    input_value = input_field.input_value() if input_field.count() > 0 else ""
                    
                    # If the payload appears outside of the input field, it should be escaped
                    if payload in search_results.replace(f'value="{payload}"', ''):
                        assert "&lt;" in search_results or "&gt;" in search_results, \
                            f"Search term not properly escaped in results with payload: {payload}"
                
                # Check for XSS in URL
                current_url = self.page.url.lower()
                if any(tag in current_url for tag in ["<script>", "javascript:"]):
                    assert False, f"Potential XSS in URL detected with payload: {payload}"
                
                # Check if search results are visible (or no results message)
                # Using more flexible selectors that should match common table/list patterns
                results_visible = False
                
                # Check for common result containers or tables
                possible_containers = [
                    "table tbody tr",  # Table rows
                    "div[role='grid']",  # Grid layout
                    "ul[role='list']",   # List layout
                    "div[class*='result']",  # Common class names
                    "div[class*='table']",   # Table containers
                    "div[class*='list']"     # List containers
                ]
                
                # Check if any of the possible containers are present and visible
                for selector in possible_containers:
                    if self.page.locator(selector).count() > 0:
                        results_visible = True
                        break
                
                # Check for common 'no results' messages if no results container found
                if not results_visible:
                    no_results_messages = [
                        "no results",
                        "no cost centers found",
                        "no matching records",
                        "no data available"
                    ]
                    
                    for message in no_results_messages:
                        if self.page.get_by_text(message, exact=False).count() > 0:
                            results_visible = True
                            break
                
                # If we still can't find results, check if the page is in a valid state
                if not results_visible:
                    # Check if the page is still interactive (no full page errors)
                    page_title = self.page.title()
                    assert "error" not in page_title.lower(), "Page shows error state"
                    
                    # Check if main content is still visible
                    main_content = self.page.locator("main, .main-content, #main, .app-content")
                    assert main_content.count() > 0, "Main content not found - page may be broken"
                    
                    # Consider it a pass if we got this far without errors
                    results_visible = True
                
                # Verify no JavaScript errors occurred
                assert len(console_errors) == 0, \
                    f"JavaScript errors occurred with payload {payload}: {console_errors}"
                    
                print(f"✓ Search handled payload safely: {description}")
                
            except Exception as e:
                # Clean up and restore original alert
                self.page.evaluate("""() => {
                    if (window.originalAlert) {
                        window.alert = window.originalAlert;
                    }
                }""")
                raise AssertionError(f"Test failed with payload '{payload}': {str(e)}")
        
        # Clean up - restore original alert handler
        self.page.evaluate("""() => {
            if (window.originalAlert) {
                window.alert = window.originalAlert;
            }
        }""")
