"""Test cases for XSS protection in Expense Type search functionality."""
import pytest
import re
from playwright.sync_api import expect, Browser, BrowserContext
from pages.expense_types.expense_types_page import ExpenseTypesPage

class TestExpenseTypeXSSSearch:
    """Test cases for XSS protection in Expense Type search."""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, logged_in_page):
        """Setup and teardown for each test."""
        self.page = logged_in_page
        self.expense_types_page = ExpenseTypesPage(self.page)
        
        # Navigate to expense types page
        self.expense_types_page.navigate()
        self.page.wait_for_load_state("networkidle")
        
        # Setup complete
        yield
        
        # Teardown - ensure clean state after all tests
        try:
            # Clear any search queries
            search_input = self.page.get_by_placeholder("Search expense types...")
            if search_input.is_visible():
                search_input.fill("")
                search_input.press("Enter")
                self.page.wait_for_load_state("networkidle")
        except Exception as e:
            print(f"Teardown warning: {str(e)}")
    
    def test_xss_in_search_field(self):
        """
        ET-013: Verify that XSS attempts in the search field are properly handled.
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
            # Basic script tags
            {"payload": "<script>alert('XSS')</script>", "description": "Basic script tag"},
            {"payload": "<script>alert(String.fromCharCode(88,83,83))</script>", "description": "Obfuscated script with String.fromCharCode"},
            
            # Event handlers and tags
            {"payload": "<img src='x' onerror='alert(1)'>", "description": "Image with onerror handler"},
            {"payload": "<svg onload='alert(1)'>", "description": "SVG with onload handler"},
            {"payload": "<body onload=alert('XSS')>", "description": "Body with onload handler"},
            
            # JavaScript URIs
            {"payload": "javascript:alert('XSS')", "description": "JavaScript URI scheme"},
            {"payload": "JaVaScRiPt:alert('XSS')", "description": "Case-varied JavaScript URI"},
            
            # DOM-based XSS
            {"payload": "\"><script>alert('XSS')</script>", "description": "Breaking out of attribute"},
            {"payload": "'; alert('XSS'); //", "description": "Breaking out of JavaScript string"},
            {"payload": "\" onmouseover=\"alert('XSS')\"", "description": "Event handler in attribute"},
            
            # Special encoding
            {"payload": "&lt;script&gt;alert('XSS')&lt;/script&gt;", "description": "HTML entity encoded"},
            {"payload": "%3Cscript%3Ealert('XSS')%3C/script%3E", "description": "URL encoded"},
            {"payload": "%22%3E%3Cscript%3Ealert('XSS')%3C/script%3E", "description": "Partially URL encoded"}
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
                search_input = self.page.get_by_placeholder("Search expense types...")
                search_input.fill("")
                
                # Enter the XSS payload in search (auto-search will trigger)
                search_input.fill(payload)
                
                # Wait for the auto-search to complete (longer debounce time)
                self.page.wait_for_timeout(1000)  # Increased wait for auto-search
                self.page.wait_for_load_state("networkidle")
                self.page.wait_for_selector("table", state="attached")  # Wait for table to update
                
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
                    pytest.fail(f"Unescaped HTML tags found in visible text with payload: {payload}")
                
                # Check if the search term is reflected in the page
                if payload in search_results:
                    # Check if it's properly escaped OR only appears in the input field value
                    input_field = self.page.locator('input[placeholder^="Search expense types"]')
                    input_value = input_field.input_value() if input_field.count() > 0 else ""
                    
                    # If the payload appears outside of the input field, it should be escaped
                    if payload in search_results.replace(f'value="{payload}"', ''):
                        assert "&lt;" in search_results or "&gt;" in search_results, \
                            f"Search term not properly escaped in results with payload: {payload}"
                
                # Check for XSS in URL
                current_url = self.page.url.lower()
                if any(tag in current_url for tag in ["<script>", "javascript:"]):
                    pytest.fail(f"Potential XSS in URL detected with payload: {payload}")
                
                # Check if search results are visible (or no results message)
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
                        "no expense types found",
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
                    if "error" in page_title.lower():
                        pytest.fail("Page shows error state")
                    
                    # Check if main content is still visible
                    main_content = self.page.locator("main, .main-content, #main, .app-content")
                    if main_content.count() == 0:
                        pytest.fail("Main content not found - page may be broken")
                
                print(f"✓ Search handled payload safely: {description}")
                
                print(f"✓ Search with payload '{payload}' did not execute JavaScript")
                
            except Exception as e:
                # Take a screenshot for debugging
                self.page.screenshot(path=f"test-results/et_xss_search_error_{payload[:10]}.png")
                
                # Get more context about the failure
                try:
                    current_url = self.page.url
                    page_title = self.page.title()
                    error_context = f"\nURL: {current_url}\nTitle: {page_title}\nError: {str(e)}"
                    print(error_context)
                except:
                    pass
                
                raise AssertionError(f"Test failed for search payload '{payload}': {str(e)}")
            finally:
                # Clear the search for the next test
                try:
                    search_input = self.page.get_by_placeholder("Search expense types...")
                    if search_input.is_visible():
                        search_input.fill("")
                        search_input.press("Enter")
                        self.page.wait_for_load_state("networkidle")
                except Exception as e:
                    print(f"Error during cleanup: {str(e)}")
