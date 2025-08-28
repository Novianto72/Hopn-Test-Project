import os
from pathlib import Path
from datetime import datetime
from typing import Union
from playwright.sync_api import Page as SyncPage

def take_screenshot(page: SyncPage, test_name: str, test_type: str = "common") -> str:
    """
    Synchronous screenshot utility.
    
    Args:
        page: Playwright page object (sync)
        test_name: Name of the test (will be part of the filename)
        test_type: Type of test (e.g., 'cost_centers', 'expense_types')
        
    Returns:
        str: Path to the saved screenshot
    """
    # Create screenshots directory if it doesn't exist
    screenshots_dir = Path("screenshots") / test_type
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamp and filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_test_name = "".join(c if c.isalnum() else "_" for c in test_name)
    filename = f"{safe_test_name}_{timestamp}.png"
    
    try:
        # Take and save screenshot
        screenshot_path = str(screenshots_dir / filename)
        page.screenshot(path=screenshot_path, full_page=True)
        return screenshot_path
    except Exception as e:
        print(f"Error taking screenshot: {str(e)}")
        # Try to save to a different location if the first attempt fails
        try:
            alt_dir = Path("test_results") / "screenshots" / test_type
            alt_dir.mkdir(parents=True, exist_ok=True)
            alt_path = str(alt_dir / filename)
            page.screenshot(path=alt_path, full_page=True)
            return alt_path
        except Exception as e2:
            print(f"Failed to save screenshot: {str(e2)}")
            return ""
