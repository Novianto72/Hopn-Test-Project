from playwright.sync_api import expect
import time
from .page_objects.home_page import HomePage

def test_keyboard_navigation(home_page):
    """Test keyboard navigation and accessibility"""
    # Initialize the page object
    home = HomePage(home_page)
    
    print("\n=== Starting accessibility test ===")
    print(f"Current URL: {home_page.url}")
    
    # Wait for page to be fully loaded (already done by fixture, but just to be safe)
    print("Waiting for page to be fully loaded...")
    home_page.wait_for_load_state('networkidle')
    time.sleep(1)  # Small wait for any dynamic content
    
    # Get focusable elements using the page object
    print("\n=== Finding all focusable elements ===")
    focusable_elements = home.get_focusable_elements()
    
    print(f"Found {len(focusable_elements)} focusable elements on the page")
    
    # Take a screenshot of the initial state
    home.take_screenshot('test-results/screenshots/accessibility_initial.png')
    
    # Test keyboard navigation
    print("\n=== Testing keyboard navigation ===")
    
    # Start with the first focusable element
    home_page.keyboard.press('Tab')
    
    # Keep track of focused elements to detect cycles
    focused_elements = []
    max_iterations = 100  # Prevent infinite loops
    
    for i in range(max_iterations):
        # Get the currently focused element
        focused = home_page.evaluate('''() => {
            const el = document.activeElement;
            if (!el) return null;
            return {
                tag: el.tagName,
                id: el.id || '',
                class: el.className || '',
                name: el.name || '',
                role: el.getAttribute('role') || '',
                text: el.textContent?.trim() || '',
                outerHTML: el.outerHTML
            };
        }''')
        
        if not focused:
            print("No element is currently focused")
            break
            
        # Print information about the focused element
        print(f"\nFocus {i+1}:")
        print(f"  Tag: {focused['tag']}")
        if focused['id']:
            print(f"  ID: #{focused['id']}")
        if focused['class']:
            print(f"  Classes: {focused['class']}")
        if focused['role']:
            print(f"  Role: {focused['role']}")
        if focused['text']:
            print(f"  Text: {focused['text'][:100]}")
            
        # Check for cycles
        if focused in focused_elements:
            print("\nDetected focus cycle. Ending navigation test.")
            break
            
        focused_elements.append(focused)
        
        # Take a screenshot of the focused element
        home.take_screenshot(f'test-results/screenshots/accessibility_focus_{i+1}.png')
        
        # Press tab to move to the next focusable element
        home_page.keyboard.press('Tab')
        
        # Small delay to ensure the focus has changed
        time.sleep(0.5)
    
    # Verify we found some focusable elements
    assert len(focused_elements) > 0, 'No focusable elements found via keyboard navigation'
    
    # If we found fewer than 5 elements, it might indicate an accessibility issue
    if len(focused_elements) < 5:
        print("\nWARNING: Fewer than 5 focusable elements found. This might indicate an accessibility issue.")
        print("Common issues include:")
        print("- Missing tabindex attributes")
        print("- Interactive elements not properly marked up")
        print("- JavaScript that modifies the tab order")
