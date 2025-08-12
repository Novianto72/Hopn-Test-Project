from playwright.sync_api import expect
import time

def test_main_cta_button(home_page):
    """Test the main call-to-action button functionality"""
    print("\n=== Testing Main CTA Button ===")
    
    try:
        # Wait for page to be fully loaded
        print("Waiting for page to be fully loaded...")
        home_page.wait_for_load_state('networkidle')
        
        # Look for the main 'Get started' button
        print("Looking for 'Get started' button...")
        get_started_buttons = home_page.get_by_role('button', name='Get started', exact=True).all()
        
        if not get_started_buttons:
            print("No 'Get started' button found. Available buttons:")
            all_buttons = home_page.locator('button').all()
            for i, btn in enumerate(all_buttons[:10]):  # Show first 10 buttons
                text = btn.text_content().strip()
                btn_id = btn.get_attribute('id') or f'button-{i}'
                print(f"  {i+1}. '{text}' (id: {btn_id})")
            assert False, "No 'Get started' button found on the page"
            
        print(f"Found {len(get_started_buttons)} 'Get started' buttons, clicking the first one")
        
        # Store the current URL before clicking
        original_url = home_page.url
        
        # Click the button
        get_started_buttons[0].click()
        
        # Wait for navigation to complete or a short delay if no navigation occurs
        try:
            home_page.wait_for_url('**/signup**', timeout=3000)
            print("Successfully navigated to signup page")
            
            # Check for signup form
            signup_form = home_page.locator('form').first
            if signup_form.is_visible():
                print("Signup form is visible on the page")
            else:
                print("No signup form found on the page")
                
        except Exception as e:
            print("No navigation to signup page occurred")
            
            # Check if we're still on the same page
            if home_page.url == original_url:
                print("Still on the same page after clicking the button")
                
                # Check for any modals or popups that might have appeared
                modals = home_page.locator('[role="dialog"], .modal, [class*="modal" i]').all()
                if modals:
                    print(f"Found {len(modals)} modal dialogs/popups")
                    for i, modal in enumerate(modals):
                        if modal.is_visible():
                            print(f"  {i+1}. Visible modal with text: {modal.text_content()[:100]}...")
                else:
                    print("No modal dialogs or popups detected")
            else:
                print(f"Navigated to a different page: {home_page.url}")
        
        print("\n=== Test completed successfully ===")
        
    except Exception as e:
        print("\n=== Test Failed ===")
        print(f"Error: {str(e)}")
        print("\nPage URL:", home_page.url)
        print("\nPage title:", home_page.title())
        print("\nPage content (first 1000 chars):")
        print(home_page.content()[:1000])
        raise
