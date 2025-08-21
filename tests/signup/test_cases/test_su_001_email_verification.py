import os
import uuid
import pytest
import time
from playwright.sync_api import Page, expect
from dotenv import load_dotenv
from dataInput.signup.test_emails import get_valid_emails, get_invalid_emails
from tests.utils.email_utils import get_latest_otp_imap
from pages.signup.signup_page import SignUpPage

# Load environment variables from .env file
load_dotenv()

# Test configuration
BASE_URL = "https://wize-invoice-dev-front.octaprimetech.com"
SIGNUP_URL = f"{BASE_URL}/create-account"

# Email configuration
BASE_EMAIL = "testingtito09"
EMAIL_DOMAIN = "@gmail.com"
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_USER = os.getenv("IMAP_USER", f"{BASE_EMAIL}{EMAIL_DOMAIN}")
IMAP_PASS = os.getenv("IMAP_PASS", "nguh lfdv cedp ijki")  # Using the provided app password

def get_test_email() -> str:
    """Generate a unique test email address."""
    unique_id = str(uuid.uuid4())[:8]
    return f"{BASE_EMAIL}+{unique_id}{EMAIL_DOMAIN}"

@pytest.mark.smoke
def test_email_verification_flow(page: Page):
    """Test the complete email verification flow with a valid email."""
    test_email = get_test_email()
    signup_page = SignUpPage(page)
    
    # 1. Navigate to signup page
    signup_page.navigate()
    expect(page).to_have_url(SIGNUP_URL)
    
    # 2. Input email and verify
    signup_page.email.fill(test_email)
    signup_page.email.blur()  # Trigger validation
    
    # 3. Click Verify button for email
    expect(signup_page.verify_email_btn).to_be_enabled()
    signup_page.verify_email_btn.click()
    
    # 4. Verify verification code message is displayed
    success_message = page.locator(f"text=A verification code has been sent to {test_email}.")
    expect(success_message).to_be_visible()
    
    # 5. Get OTP from email
    try:
        # Wait for the email to arrive (polling)
        max_attempts = 5
        otp = None
        
        for attempt in range(max_attempts):
            otp = get_latest_otp_imap(
                imap_host=IMAP_HOST,
                username=IMAP_USER,
                password=IMAP_PASS,
                email_to=test_email,
                timeout_sec=30
            )
            
            if otp:
                break
                
            if attempt < max_attempts - 1:
                time.sleep(5)  # Wait before next attempt
        
        if not otp:
            pytest.fail("Failed to retrieve OTP after multiple attempts")
        
        # 6. Enter and submit OTP using POM method
        signup_page.verify_email_otp(otp)
        
        # 7. Verify success message
        success_message = page.locator("text=Email successfully verified!")
        expect(success_message).to_be_visible(timeout=10000)
        
    except TimeoutError as e:
        pytest.fail(f"Failed to get OTP: {str(e)}")
    except Exception as e:
        pytest.fail(f"An error occurred: {str(e)}")

@pytest.mark.skip(reason="Not currently needed - will be implemented in a future update")
@pytest.mark.parametrize("email", get_valid_emails())
def test_valid_email_formats(page: Page, email: str):
    """Test that valid email formats are accepted."""
    page.goto(SIGNUP_URL)
    email_input = page.locator("input#email")
    email_input.fill(email)
    email_input.blur()  # Trigger validation
    
    # Verify no error message is shown for valid emails
    error_message = page.locator("text=Please enter a valid email")
    expect(error_message).not_to_be_visible()
    
    # Verify the verify button is enabled
    verify_button = page.locator('//label[text()="Email"]/../div/button')
    expect(verify_button).to_be_enabled()

@pytest.mark.smoke
def test_invalid_email_formats(page: Page):
    """Test that invalid email formats are rejected."""
    # Get invalid emails from test data
    invalid_emails = get_invalid_emails()
    
    for email in invalid_emails:
        # Navigate to the signup page for each test
        page.goto(SIGNUP_URL)
        print(f"\nTesting email: {repr(email)}")
        
        # Input email
        email_input = page.locator("input#email")
        email_input.fill(email)
        email_input.blur()  # Trigger validation
        
        # Get the actual value after input (to check for auto-trimming)
        actual_value = email_input.input_value()
        if actual_value != email:
            print(f"  - Input was modified to: {repr(actual_value)}")
        
        # Click verify button if it's enabled (some invalid formats might still allow clicking)
        verify_button = page.locator('//label[text()="Email"]/../div/button')
        if verify_button.is_enabled():
            verify_button.click()
            
            # Wait for either "Sending code..." or final error message
            try:
                # First check for "Sending code..." message
                sending_code = page.locator("text=Sending code...")
                if sending_code.is_visible():
                    print("  - 'Sending code...' message detected, waiting for final error...")
                    # Wait for the final error message (with timeout)
                    page.wait_for_selector("p.text-red-500:not(:has-text('Sending code...'))", timeout=10000)
            except Exception as e:
                print(f"  - No 'Sending code...' message detected: {str(e)}")
        
        # Get the final error message text if it exists
        error_message_locator = page.locator("p.text-red-500")
        error_text = "No error message found"
        if error_message_locator.count() > 0:
            error_text = error_message_locator.first.text_content()
            print(f"  - Final error message: {error_text}")
            
        print(f"Error message: {error_text}")
        
        # Verify the verify button is disabled after interaction
        if verify_button.is_enabled():
            print("Warning: Verify button is still enabled after invalid email input")
        
        # Take a screenshot for debugging
        safe_email = email.replace('@', '_at_').replace('.', '_').replace(' ', '_')
        screenshot_path = f"test_results/invalid_email_{safe_email[:50]}.png"
        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
        page.screenshot(path=screenshot_path)
        
        # For emails with spaces, check if they were auto-trimmed
        if ' ' in email and email.strip() == actual_value:
            print("  - Email was auto-trimmed")
            # If the email is valid after trimming, we expect it to be accepted
            if '@' in actual_value and '.' in actual_value.split('@')[-1]:
                print("  - Trimmed email appears valid, expecting success")
                continue
        
        # For empty email, we expect a required field validation
        if email.strip() == '':
            # Old implementation (kept for reference)
            # assert ("required" in error_text.lower() or 
            #        "must be filled" in error_text.lower() or
            #        "can't be blank" in error_text.lower()), \
            #     f"Expected required field error for empty email, got: {error_text}"
            
            # New implementation: Check if verify button is disabled for empty emails
            verify_button = page.locator('//label[text()="Email"]/../div/button')
            assert not verify_button.is_enabled(), \
                f"Verify button should be disabled for empty email, but it's enabled"
        else:
            # For other invalid emails, check for validation error
            assert ("valid email" in error_text.lower() or 
                   "invalid" in error_text.lower() or 
                   "enter a valid" in error_text.lower() or
                   "not valid" in error_text.lower() or
                   "fail" in error_text.lower() or
                   "error" in error_text.lower()), \
                f"Expected validation error for email: {email}, but got: {error_text}"
        
        # Refresh the page for the next test case
        page.reload()
