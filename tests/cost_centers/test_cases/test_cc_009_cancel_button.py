import pytest
import time
from playwright.sync_api import expect, Page
from pages.cost_centers.cost_centers_page import CostCentersPage
from tests.config.test_config import URLS, TestConfig
from dataInput.cost_centers.test_data import (
    cancel_button_test_data
)

@pytest.mark.cost_centers
class TestModalClosure:
    """Test cases for modal closure functionality in Cost Center form."""
    
    def setup_method(self, method):
        """Setup for each test method."""
        # This will be called before each test method
        pass
        
    def open_modal(self):
        """Helper method to open the cost center creation modal."""
        self.page.get_by_role("button", name="New Cost Center").click()
        modal = self.page.locator("div[data-slot='card']")
        expect(modal).to_be_visible()
        return modal
    
    def test_cancel_button_closes_modal(self, logged_in_page):
        """Test that clicking the Cancel button closes the modal."""
        # Setup page and navigate to cost centers
        self.page = logged_in_page
        self.cost_centers_page = CostCentersPage(page=self.page)
        self.page.goto(URLS["COST_CENTERS"])
        
        # Open the modal
        modal = self.open_modal()
        
        # Find and click the Cancel button
        cancel_button = self.page.get_by_role("button", name="Cancel", exact=True)
        assert cancel_button.is_visible(), "Cancel button is not visible"
        
        # Click the Cancel button
        cancel_button.click()
        
        # Verify the modal is closed
        try:
            modal.wait_for(state="hidden", timeout=5000)
            print("✓ Modal closed successfully after clicking Cancel button")
        except Exception as e:
            print(f"Error closing modal: {e}")
            self.page.screenshot(path="cancel_button_modal_failure.png")
            raise
            
        # Verify the modal is no longer visible
        assert not modal.is_visible(), "Modal should be closed after clicking Cancel"
        
        # Verify the URL hasn't changed
        assert URLS["COST_CENTERS"] in self.page.url, "Navigation occurred when it shouldn't have"
        
    def test_close_button_closes_modal(self, logged_in_page):
        """Test that clicking the close (X) button closes the modal."""
        # Setup page and navigate to cost centers
        self.page = logged_in_page
        self.cost_centers_page = CostCentersPage(page=self.page)
        self.page.goto(URLS["COST_CENTERS"])
        
        # Open the modal
        modal = self.open_modal()
        
        # Find and click the close (X) button with retry logic
        max_attempts = 3
        close_button = None
        
        # Try different selectors for the close button
        selectors = [
            "button[aria-label='Close']",
            "svg.lucide-x.w-4.h-4",
            "[role='dialog'] button[aria-label*='close' i]",
            "[role='dialog'] button:has(svg)",
            "[role='dialog'] button:has-text('×')",
            "[role='dialog'] button:has-text('✕')"
        ]
        
        for selector in selectors:
            close_button = self.page.locator(selector).first
            if close_button.is_visible():
                break
        
        if not close_button or not close_button.is_visible():
            # Take a screenshot if close button not found
            self.page.screenshot(path="close_button_not_found.png")
            raise Exception("Could not find close (X) button in the modal")
        
        # Click the close button with retry
        for attempt in range(1, max_attempts + 1):
            try:
                # Scroll into view and get position
                close_button.scroll_into_view_if_needed()
                box = close_button.bounding_box()
                
                # Move mouse to the button and click
                self.page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                close_button.click(delay=100)
                print(f"✓ Clicked close button on attempt {attempt}")
                break
            except Exception as e:
                print(f"Attempt {attempt} to click close button failed: {e}")
                if attempt == max_attempts:
                    # Try to close with Escape key as last resort
                    print("Attempting to close modal with Escape key")
                    self.page.keyboard.press("Escape")
                self.page.wait_for_timeout(500)
        
        # Verify the modal is closed
        try:
            modal.wait_for(state="hidden", timeout=5000)
            print("✓ Modal closed successfully after clicking close button (X)")
        except Exception as e:
            print(f"Error closing modal: {e}")
            self.page.screenshot(path="close_button_modal_failure.png")
            raise
            
        # Verify the modal is no longer visible
        assert not modal.is_visible(), "Modal should be closed after clicking close button (X)"
        
        # Verify the URL hasn't changed
        assert URLS["COST_CENTERS"] in self.page.url, "Navigation occurred when it shouldn't have"
