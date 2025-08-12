from playwright.sync_api import expect
import time
import os

def test_responsive_design(home_page):
    """Test the page layout across different screen sizes"""
    # Create screenshots directory if it doesn't exist
    os.makedirs('test-results/screenshots/responsive', exist_ok=True)
    
    viewports = [
        {'width': 375, 'height': 667, 'name': 'mobile'},    # iPhone 8
        {'width': 768, 'height': 1024, 'name': 'tablet'},   # iPad
        {'width': 1366, 'height': 768, 'name': 'laptop'},   # Common laptop
        {'width': 1920, 'height': 1080, 'name': 'desktop'}  # Full HD
    ]
    
    for viewport in viewports:
        print(f"\nTesting viewport: {viewport['name']} ({viewport['width']}x{viewport['height']})")
        
        # Set viewport size
        home_page.set_viewport_size(viewport)
        
        # Wait for any potential layout shifts
        time.sleep(1)
        
        # Test key elements visibility
        print("  - Checking header visibility...")
        header = home_page.locator('header').or_(home_page.get_by_role('banner'))
        expect(header).to_be_visible()
        
        # Check for interactive elements
        print("  - Checking interactive elements...")
        interactive_elements = home_page.locator('button, a[href]').all()
        
        # Check for navigation elements
        print("  - Checking navigation...")
        nav = home_page.locator('nav').or_(home_page.get_by_role('navigation')).first
        
        if viewport['width'] < 768:  # Mobile/tablet
            # Look for a menu toggle button
            menu_buttons = home_page.get_by_role('button', name='Menu').or_(
                home_page.locator('button:has-text("Menu")')
            ).all()
            
            if menu_buttons:
                print("  - Found menu button (mobile navigation)")
                # Click the menu to test if it expands
                try:
                    menu_buttons[0].click()
                    time.sleep(0.5)  # Wait for menu animation
                    # Check if navigation links become visible
                    nav_links = nav.locator('a').all()
                    if nav_links:
                        print(f"  - Found {len(nav_links)} navigation links in mobile menu")
                except Exception as e:
                    print(f"  - Could not interact with menu button: {str(e)}")
        else:  # Desktop
            # Look for visible navigation links
            nav_links = nav.locator('a').filter(has_not=home_page.locator('[style*="display: none"]')).all()
            if nav_links:
                print(f"  - Found {len(nav_links)} visible navigation links")
            else:
                print("  - Warning: No visible navigation links found in desktop view")
        
        # Check for main content sections
        print("  - Checking main content sections...")
        main_sections = ['hero', 'features', 'pricing', 'testimonials', 'cta', 'footer']
        for section in main_sections:
            section_locator = home_page.locator(f'section#{section}').or_(
                home_page.locator(f'[data-testid="{section}"]')
            )
            if section_locator.count() > 0:
                print(f"  - Found section: {section}")
        
        # Take screenshot for visual reference
        screenshot_path = f'test-results/screenshots/responsive/{viewport["name"]}.png'
        home_page.screenshot(path=screenshot_path)
        print(f"  - Screenshot saved to: {screenshot_path}")
        
        # Scroll to bottom to trigger any lazy-loaded content
        home_page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        time.sleep(0.5)  # Wait for any lazy loading
        
    print("\nResponsive test completed successfully!")
