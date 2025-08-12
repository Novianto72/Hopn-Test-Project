from playwright.sync_api import expect, Page
import time
from conftest import LOGIN_URL

def test_login_page_load_time(login_page: Page):
    """Test login page load performance"""
    print("\n=== Testing Login Page Load Time ===")
    
    try:
        # Measure load time
        start_time = time.time()
        login_page.goto(LOGIN_URL)
        end_time = time.time()
        
        # Calculate load time
        load_time = end_time - start_time
        print(f"Page load time: {load_time:.2f} seconds")
        
        # Verify page is fully loaded
        email_field = login_page.get_by_label("Email")
        password_field = login_page.get_by_label("Password")
        login_button = login_page.get_by_role("button", name="Login")
        
        expect(email_field).to_be_visible()
        expect(password_field).to_be_visible()
        expect(login_button).to_be_visible()
        
        # Assert load time is reasonable
        assert load_time < 5, "Page load time is too long"
        
        print("\n=== Test completed successfully ===")
        
    except Exception as e:
        print("\n=== Test Failed ===")
        print(f"Error: {str(e)}")
        print("\nPage content:")
        print(login_page.content()[:1000])
        raise

def test_login_page_keyboard_navigation(login_page: Page):
    """Test keyboard navigation on login page"""
    print("\n=== Testing Keyboard Navigation ===")
    
    try:
        # Navigate to login page
        login_page.goto(LOGIN_URL)
        login_page.wait_for_load_state('networkidle')
        
        # Get form elements
        email_field = login_page.get_by_label("Email")
        # Updated to match the actual text in the DOM
        forgot_password_link = login_page.get_by_role("link", name="Forgot password?")
        password_field = login_page.get_by_label("Password")
        login_button = login_page.locator('//button[text()="Login"]')
        
        # Test tab order
        print("\nTesting tab order...")
        
        # Start with email field focused
        email_field.focus()
        expect(email_field).to_be_focused()
        print("1. Email field has focus")
        
        # Tab to Forgot Password link
        email_field.press("Tab")
        expect(forgot_password_link).to_be_focused()
        print("2. Forgot Password link has focus")
        
        # Tab to Password field
        forgot_password_link.press("Tab")
        expect(password_field).to_be_focused()
        print("3. Password field has focus")
        
        # Tab to password toggle button first, then to Login button
        password_field.press("Tab")
        print("4. Tabbed to password toggle button")
        
        # Tab again to reach Login button
        login_page.keyboard.press("Tab")
        expect(login_button).to_be_focused()
        print("5. Login button has focus")
        
        # Verify tab does not wrap back to email field
        login_button.press("Tab")
        expect(login_button).not_to_be_focused()
        print("5. Focus moved away from Login button (no wrap to email field)")
        
        print("\n=== Test completed successfully ===\n")
        
    except Exception as e:
        print("\n=== Test Failed ===")
        print(f"Error: {str(e)}")
        print("\nPage content:")
        print(login_page.content()[:1000])
        raise

def test_login_page_error_feedback(login_page: Page):
    """Verify user remains on login page after failed login attempts"""
    print("\n=== Testing Login Page Error Handling ===")
    
    try:
        # Wait for page load
        login_page.wait_for_load_state('domcontentloaded')
        
        # Test various error scenarios
        test_cases = [
            {
                "name": "Empty fields",
                "email": "",
                "password": ""
            },
            {
                "name": "Invalid email format",
                "email": "invalid-email",
                "password": "password123"
            },
            {
                "name": "Incorrect credentials",
                "email": "nonexistent@example.com",
                "password": "wrongpassword"
            }
        ]
        
        for case in test_cases:
            print(f"\nTesting scenario: {case['name']}")
            
            # Fill in invalid credentials
            email_field = login_page.get_by_label("Email")
            password_field = login_page.get_by_label("Password")
            login_button = login_page.get_by_role("button", name="Login")
            
            # Get current URL before login attempt
            initial_url = login_page.url
            
            # Fill form fields and submit
            if case["email"]:
                email_field.fill(case["email"])
            if case["password"]:
                password_field.fill(case["password"])
            
            login_button.click()
            
            # Wait for any potential navigation to complete
            login_page.wait_for_load_state('networkidle')
            
            # Verify we're still on the login page
            current_url = login_page.url
            assert "login" in current_url.lower(), f"Expected to remain on login page, but was redirected to {current_url}"
            
            # Verify form is still present and interactive
            expect(email_field).to_be_visible()
            expect(password_field).to_be_visible()
            expect(login_button).to_be_visible()
            
            # Clear fields for next test case
            email_field.fill("")
            password_field.fill("")
            
        print("\n=== Test completed successfully ===")
        
    except Exception as e:
        print("\n=== Test Failed ===")
        print(f"\n=== Test Failed ===")
        print(f"Error: {str(e)}")
        raise

def test_login_page_element_visibility(login_page: Page):
    # Test visibility and alignment of login page elements
    print("\n=== Testing Element Visibility ===")
    
    try:
        # Navigate to login page
        login_page.goto(LOGIN_URL)
        login_page.wait_for_load_state('networkidle')
        
        # Get all elements to check with specific selectors
        email_field = login_page.get_by_label("Email")
        password_field = login_page.get_by_label("Password")
        login_button = login_page.locator('//button[text()="Login"]')
        
        # Use more specific selectors for links
        sign_up_link = login_page.get_by_role("link", name="Sign Up").first
        forgot_password_link = login_page.get_by_role("link", name="Forgot password?")
        
        elements = {
            "Email Input": email_field,
            "Password Input": password_field,
            "Login Button": login_button,
            "Sign Up Link": sign_up_link,
            "Forgot Password Link": forgot_password_link
        }      
        for name, element in elements.items():
            print(f"\nVerifying {name}...")
            # Wait for element to be visible
            element.wait_for(state="visible", timeout=5000)
            expect(element).to_be_visible()
            
            # Check element alignment
            position = element.evaluate("""
                (el) => {
                    const rect = el.getBoundingClientRect();
                    return {
                        top: rect.top,
                        left: rect.left,
                        width: rect.width,
                        height: rect.height
                    };
                }
            """)
            
            print(f"Position: {position}")
            
            # Verify element is within viewport
            viewport = login_page.evaluate("""
                () => {
                    return {
                        width: window.innerWidth,
                        height: window.innerHeight
                    };
                }
            """)
            
            assert position["top"] >= 0 and position["top"] <= viewport["height"], \
                f"{name} is not within viewport vertically"
            assert position["left"] >= 0 and position["left"] <= viewport["width"], \
                f"{name} is not within viewport horizontally"
            
        print("\n=== Test completed successfully ===")
        
    except Exception as e:
        print(f"\n=== Test Failed ===")
        print(f"Error: {str(e)}")
        raise
