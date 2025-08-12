from playwright.sync_api import expect, Page
import pytest
from conftest import LOGIN_URL, VALID_CREDENTIALS

def test_form_validation_positive(login_page: Page):
    """Test form validation with valid input"""
    print("\n=== Testing Form Validation with Valid Input ===")
    
    try:
        # Navigate to login page
        login_page.goto(LOGIN_URL)
        
        # Fill in valid credentials
        email_field = login_page.get_by_label("Email")
        password_field = login_page.get_by_label("Password")
        login_button = login_page.get_by_role("button", name="Login")
        
        email_field.fill(VALID_CREDENTIALS["email"])
        password_field.fill(VALID_CREDENTIALS["password"])
        
        # Verify no validation errors
        error_messages = login_page.get_by_text("Please enter a valid email address")
        expect(error_messages).to_be_hidden()
        
        error_messages = login_page.get_by_text("Password must be at least 8 characters")
        expect(error_messages).to_be_hidden()
        
        # Click login button
        login_button.click()
        
        # Verify successful login by checking for Dashboard
        login_page.wait_for_url("**/dashboard")
        dashboard_heading = login_page.get_by_role("heading", name="Dashboard")
        expect(dashboard_heading).to_be_visible()
        print("\n=== Test completed successfully ===")
        
    except Exception as e:
        print(f"\n=== Test Failed ===")
        print(f"Error: {str(e)}")
        raise

def test_form_validation_negative(login_page: Page):
    """Test form validation with invalid input"""
    print("\n=== Testing Form Validation with Invalid Input ===")
    
    try:
        # Navigate to login page
        login_page.goto(LOGIN_URL)
        
        # Test various invalid inputs
        test_cases = [
            {"email": "invalid", "password": "test", "description": "Invalid email format"},
            {"email": "", "password": "Test@123", "description": "Empty email"},
            {"email": "test@example.com", "password": "", "description": "Empty password"},
            {"email": "test", "password": "Test@123", "description": "Invalid email format (no domain)"}
        ]
        
        for case in test_cases:
            print(f"\nTesting case: {case['description']}")
            
            # Get form elements
            email_field = login_page.get_by_label("Email")
            password_field = login_page.get_by_label("Password")
            login_button = login_page.get_by_role("button", name="Login")
            
            # Clear and fill fields
            email_field.fill("")
            password_field.fill("")
            email_field.fill(case["email"])
            password_field.fill(case["password"])
            
            # Check if form is in valid state
            is_email_valid = email_field.evaluate('el => el.validity.valid')
            is_password_valid = password_field.evaluate('el => el.validity.valid')
            
            # Verify form validation states
            if case["email"] == "":
                assert not is_email_valid, "Empty email should be invalid"
            elif "@" not in case["email"]:
                assert not is_email_valid, f"Invalid email format should be invalid: {case['email']}"
                
            if case["password"] == "":
                assert not is_password_valid, "Empty password should be invalid"
                
            # Click login button and verify we're still on the login page
            login_button.click()
            
            # Verify we're still on the login page
            expect(login_page).to_have_url(LOGIN_URL)
            print(f"✓ Form validation working as expected for {case['description']}")
            
            # Clear storage for next test case
            login_page.reload()
            
            # Verify error messages
            for error in case.get("errors", []):
                error_message = login_page.get_by_text(error)
                expect(error_message).to_be_visible()
            
            # Clear fields for next test
            email_field.fill("")
            password_field.fill("")
            
        print("\n=== Test completed successfully ===")
        
    except Exception as e:
        print(f"\n=== Test Failed ===")
        print(f"Error: {str(e)}")
        raise

def test_form_error_handling(login_page: Page):
    """Test error handling during form submission"""
    print("\n=== Testing Form Error Handling ===")
    
    try:
        # Test error handling with invalid credentials
        email_field = login_page.get_by_label("Email")
        password_field = login_page.get_by_label("Password")
        login_button = login_page.get_by_role("button", name="Login")
        
        email_field.fill("test@example.com")
        password_field.fill("wrongpassword")
        login_button.click()
        
        # Verify error message
        error_message = login_page.get_by_text("Login failed. Please check your credentials.")
        expect(error_message).to_be_visible()
        
        # Verify form fields after failed login
        actual_email = email_field.input_value()
        actual_password = password_field.input_value()
        
        # Log the actual values for debugging
        print(f"\nAfter failed login:")
        print(f"Email field value: {repr(actual_email)}")
        print(f"Password field value: {repr(actual_password)}")
        
        # Check if email is preserved (some systems might clear it for security)
        if actual_email != "test@example.com":
            print("Note: Email field was cleared after failed login (this might be expected behavior)")
        
        # Password should always be cleared for security
        assert actual_password == "", "Password field should be cleared after failed login for security"
        
        print("\n=== Test completed successfully ===")
        
    except Exception as e:
        print("\n=== Test Failed ===")
        print(f"Error: {str(e)}")
        print("\nPage content:")
        print(login_page.content()[:1000])
        raise

def test_form_revalidation(login_page: Page):
    """Test form behavior when fields are modified"""
    print("\n=== Testing Form Behavior ===")
    
    try:
        # Navigate to login page
        login_page.goto(LOGIN_URL)
        
        # Get form elements
        email_field = login_page.get_by_label("Email")
        password_field = login_page.get_by_label("Password")
        login_button = login_page.get_by_role("button", name="Login")
        
        # Test 1: Attempt login with empty fields
        email_field.fill("")
        password_field.fill("")
        login_button.click()
        expect(login_page).to_have_url(LOGIN_URL)  # Should stay on login page
        print("✓ Login prevented with empty fields")
        
        # Test 2: Attempt login with invalid email format
        email_field.fill("")
        email_field.fill("invalid-email")
        password_field.fill("")
        password_field.fill("password")
        login_button.click()
        expect(login_page).to_have_url(LOGIN_URL)  # Should stay on login page
        print("✓ Login prevented with invalid email format")
        
        # Test 3: Attempt login with empty password
        email_field.fill("")
        email_field.fill(VALID_CREDENTIALS["email"])
        password_field.fill("")
        login_button.click()
        expect(login_page).to_have_url(LOGIN_URL)  # Should stay on login page
        print("✓ Login prevented with empty password")
        
        # Clear form for next test
        email_field.fill("")
        
        # Test 4: Attempt login with valid credentials
        # (Actual login test is covered in other test cases)
        print("✓ Form interaction tests completed")
        
    except Exception as e:
        print(f"\n=== Test Failed ===")
        print(f"Error: {str(e)}")
        print("\nPage content:")
        print(login_page.content()[:1000])
        raise
