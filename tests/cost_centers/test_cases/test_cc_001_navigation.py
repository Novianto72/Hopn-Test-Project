import time
import pytest
from playwright.sync_api import expect, Page
from pages.cost_centers.cost_centers_page import CostCentersPage
from tests.config.test_config import URLS
from dataInput.cost_centers.test_data import credentials, navigation_test_data

class TestCostCentersNavigation:
    """Test cases for Cost Centers navigation functionality."""
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Setup test with a logged-in page."""
        self.page = page
        
        # Login
        self.page.goto(URLS["LOGIN"])
        self.page.get_by_label("Email").fill(credentials["email"])
        self.page.get_by_label("Password").fill(credentials["password"])
        self.page.get_by_role("button", name="Login").click()
        self.page.wait_for_url(URLS["DASHBOARD"])
        
        # Create page object
        self.cost_centers_page = CostCentersPage(self.page)
    
    def test_navigation_to_cost_centers(self):
        """CC-001: Verify navigation to 'Cost Centers' page from sidebar"""
        try:
            print("\n=== Starting navigation test...")
            
            # Wait for sidebar to be interactive
            self.page.wait_for_load_state("domcontentloaded")
            
            # Click on Cost Centers in the sidebar with retry
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    print(f"Attempt {attempt + 1} to click Cost Centers link...")
                    sidebar_item = self.page.get_by_role("link", name="Cost Centers", exact=True)
                    sidebar_item.click(timeout=10000)
                    
                    # Wait for navigation to complete
                    try:
                        self.page.wait_for_url("**/cost-center", timeout=15000)
                        print("✓ Successfully navigated to Cost Centers")
                        break
                    except Exception as e:
                        print(f"Navigation verification failed: {e}")
                        if attempt == max_retries - 1:
                            raise
                        
                except Exception as e:
                    print(f"Click attempt {attempt + 1} failed: {e}")
                    if attempt == max_retries - 1:
                        # Screenshot functionality has been disabled as per user request
                        # self.page.screenshot(path="navigation_error.png")
                        # print("✗ Screenshot saved as navigation_error.png")
                        raise
                    
                    # Wait before retry
                    time.sleep(2)
            
            # Wait for page to be interactive
            self.page.wait_for_load_state("domcontentloaded")
            
            # Screenshot functionality has been disabled as per user request
            # self.page.screenshot(path="cost_centers_page.png")
            # print("✓ Screenshot saved as cost_centers_page.png")
            
            # Verify URL
            expect(self.page).to_have_url(navigation_test_data["expected_url"])
            
            # Verify page content is loaded
            print("Verifying page elements...")
            
            # Check for page title with flexible matching
            page_title = self.page.get_by_role("heading", name=navigation_test_data["page_title"]).first
            if page_title.is_visible():
                print(f"✓ Found page title: {page_title.text_content()}")
            else:
                print(f"Warning: Could not find main page heading: {navigation_test_data['page_title']}")
            
            # Verify all expected elements are present
            for element in navigation_test_data["elements_to_verify"]:
                try:
                    # Wait for the element to be present in the DOM first
                    self.page.wait_for_selector(element["selector"], state="attached", timeout=10000)
                    
                    # Get the element
                    element_locator = self.page.locator(element["selector"]).first
                    
                    # Wait for the element to be visible
                    element_locator.wait_for(state="visible", timeout=10000)
                    
                    # Additional check for visibility
                    if not element_locator.is_visible():
                        raise Exception(f"Element is not visible: {element['description']}")
                        
                    print(f"✓ Found {element['description']}")
                    
                except Exception as e:
                    # Get more context about the current page state
                    print(f"\n=== Error finding {element['description']} ===")
                    print(f"Selector used: {element['selector']}")
                    print(f"Current URL: {self.page.url}")
                    print(f"Page title: {self.page.title()}")
                    print("\nAvailable buttons on page:")
                    buttons = self.page.locator('button').all()
                    for i, btn in enumerate(buttons[:10]):  # Show first 10 buttons
                        try:
                            print(f"Button {i+1}: {btn.text_content()}")
                        except:
                            print(f"Button {i+1}: [could not get text]")
                    
                    print("\nAvailable input fields:")
                    inputs = self.page.locator('input').all()
                    for i, inp in enumerate(inputs[:10]):  # Show first 10 inputs
                        try:
                            placeholder = inp.get_attribute('placeholder') or '[no placeholder]'
                            print(f"Input {i+1}: placeholder='{placeholder}'")
                        except:
                            print(f"Input {i+1}: [could not get details]")
                    
                    raise Exception(f"Failed to find {element['description']} using selector: {element['selector']}. Error: {str(e)}")
            
            print("\n✓ Test completed successfully")
            
        except Exception as e:
            # Screenshot functionality has been disabled as per user request
            # self.page.screenshot(path="test_failure.png")
            print("\n=== Test Failed ===")
            # print("Screenshot saved as test_failure.png")
            print("Screenshot saved as test_failure.png")
            print("\nPage content (first 2000 chars):")
            print(self.page.content()[:2000])
            raise
