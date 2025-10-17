import pytest
import time
from playwright.sync_api import Page, expect
from pages.expense_types.expense_types_page import ExpenseTypesPage
from tests.page_components.table_component import TableComponent

class BaseExpenseTypeTest:
    """Base test class with common utilities for expense type tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self, logged_in_page: Page):
        """Setup test environment"""
        self.page = logged_in_page
        self.expense_types_page = ExpenseTypesPage(self.page)
        
        # Navigate to the expense types page
        self.expense_types_page.navigate()
        
        # Verify the page is loaded
        from tests.config.test_config import URLS
        expect(self.page).to_have_url(URLS["EXPENSE_TYPE"])
        expect(self.page.locator("h1")).to_have_text("Expense Types")
        
        # Setup request monitoring after navigation
        self._setup_request_monitoring()
        
        # Initialize table component
        self.table = TableComponent(self.page)
        
        # Wait for any initial data to load
        self.page.wait_for_load_state("networkidle")
        yield
        
    def _setup_request_monitoring(self):
        """Setup request/response monitoring for debugging"""
        self.failed_requests = []
        
        def handle_response(response):
            if response.status >= 400:
                self.failed_requests.append({
                    'url': response.url,
                    'status': response.status,
                    'method': response.request.method,
                    'headers': dict(response.request.headers),
                    'response_headers': dict(response.headers)
                })
        
        self.page.on("response", handle_response)
    
    def check_for_server_errors(self, timeout=10000):
        """Check for server error pages and reload if needed.
        
        Args:
            timeout: Maximum time to wait for page reload (ms)
        Returns:
            bool: True if server error was detected and handled, False otherwise
        """
        try:
            # Check for common error messages
            error_indicators = [
                "This page isn't working right now",
                "500 Internal Server Error",
                "Service Unavailable",
                "Server Error",
                "Something went wrong"
            ]
            
            # Get page content with a short timeout
            content = self.page.content(timeout=5000)
            
            # Check for any error indicators
            if any(error in content for error in error_indicators):
                print("Server error detected, attempting to reload...")
                self.page.reload()
                # Wait for the page to be interactive
                self.page.wait_for_load_state('domcontentloaded')
                self.page.wait_for_selector('body', state='visible', timeout=timeout)
                return True
            return False
        except Exception as e:
            print(f"Error checking for server errors: {str(e)}")
            return False
    
    def is_page_healthy(self):
        """Check if the current page is in a healthy state"""
        try:
            return self.page.evaluate("""() => {
                return document.readyState === 'complete' && 
                       !document.title.includes('Error') &&
                       !document.body.innerText.includes('Error');
            }""")
        except:
            return False
    
    def ensure_page_loaded(self, timeout=30000):
        """Ensure the page is fully loaded and healthy"""
        try:
            # Check for server errors first
            if self.check_for_server_errors():
                return False
                
            # Wait for the page to be interactive
            self.page.wait_for_load_state('domcontentloaded')
            
            # Wait for the main content to be visible
            self.page.wait_for_selector('body', state='visible', timeout=timeout)
            
            # Check if page is healthy
            if not self.is_page_healthy():
                print("Page is not in a healthy state")
                return False
                
            return True
        except Exception as e:
            print(f"Error ensuring page loaded: {str(e)}")
            return False
    
    def take_screenshot(self, name):
        """Screenshot functionality is disabled"""
        # Screenshot functionality has been disabled as per user request
        # import os
        # os.makedirs('test-results', exist_ok=True)
        # path = f"test-results/{name}_{int(time.time())}.png"
        # self.page.screenshot(path=path)
        # return path
        return ""
