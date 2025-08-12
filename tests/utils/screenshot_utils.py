import os
from pathlib import Path
from datetime import datetime
from playwright.sync_api import Page

def take_screenshot(page: Page, test_name: str, test_type: str = "common"):
    """
    Take a screenshot and save it in the appropriate directory.
    
    Args:
        page: Playwright page object
        test_name: Name of the test (will be part of the filename)
        test_type: Type of test (e.g., 'cost_centers', 'expense_types')
    """
    # Create screenshots directory if it doesn't exist
    screenshots_dir = Path("screenshots") / test_type
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamp and filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_test_name = "".join(c if c.isalnum() else "_" for c in test_name)
    filename = f"{safe_test_name}_{timestamp}.png"
    
    # Take and save screenshot
    screenshot_path = str(screenshots_dir / filename)
    page.screenshot(path=screenshot_path)
    
    return screenshot_path
