import os
import re
import time
import pytest
import string
import random
from dotenv import load_dotenv
from playwright.sync_api import Page, expect
from pages.reset_password.reset_password_page import ResetPasswordPage
from tests.config.test_config import URLS, CREDENTIALS
from dataInput.reset_password.test_reset_password_data import get_test_user
from tests.utils.email_utils import get_latest_otp_imap

# Load environment variables from .env file
load_dotenv()

# Test configuration
BASE_EMAIL = "testingtito09"
EMAIL_DOMAIN = "@gmail.com"
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_USER = os.getenv("IMAP_USER", f"{BASE_EMAIL}{EMAIL_DOMAIN}")
IMAP_PASS = os.getenv("IMAP_PASS", "nguh lfdv cedp ijki")  # Using the provided app password

@pytest.mark.reset_password
class TestResetPasswordFlow:
    def generate_random_password(self, length=12):
        """Generate a random password with letters, digits, and special characters."""
        # Define character sets
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = '!@#$%^&*()_+=-[]{}|;:,.<>?'
        
        # Ensure at least one character from each set
        password = [
            random.choice(lowercase),
            random.choice(uppercase),
            random.choice(digits),
            random.choice(special)
        ]
        
        # Fill the rest of the password
        all_chars = lowercase + uppercase + digits + special
        password.extend(random.choice(all_chars) for _ in range(length - 4))
        
        # Shuffle the password to make it more random
        random.shuffle(password)
        return ''.join(password)

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Initialize the page objects and navigate to the reset password page."""
        self.page = page
        self.base_url = URLS['HOME']
        self.reset_password_page = ResetPasswordPage(page).navigate_to_reset_password(self.base_url)
        self.test_user = get_test_user()
        # Generate a new random password for this test run
        self.new_password = self.generate_random_password(12)

    def test_reset_password_happy_flow(self):
        """Test the complete reset password flow with valid data."""
        print("Starting test_reset_password_happy_flow...")
        
        # 1. Request reset code with email
        email = self.test_user["email"]
        print(f"Requesting password reset code for email: {email}")
        self.reset_password_page.request_reset_code(email)
        
        # 2. Verify success message with the email
        print("Verifying success message...")
        success_message = self.reset_password_page.page.locator(
            f"p.text-sm.font-medium:has-text('A password reset code has been sent to {email}')"
        )
        expect(success_message).to_be_visible(timeout=10000)
        
        # 3. Wait for OTP field to be visible with retry logic
        print("Waiting for OTP field to be visible...")
        otp_visible = self.reset_password_page.wait_for_otp_field(max_retries=6, retry_delay=5)
        assert otp_visible, "OTP field did not become visible after multiple retries"
        
        # 4. Get OTP from email
        print("Retrieving OTP from email...")
        max_attempts = 5
        otp = None
        
        print(f"\n=== OTP Retrieval Debug ===")
        print(f"IMAP Host: {IMAP_HOST}")
        print(f"IMAP User: {IMAP_USER}")
        print(f"Email to check: {email}")
        print("Attempting to retrieve OTP...")
    
        for attempt in range(max_attempts):
            print(f"\nAttempt {attempt + 1}/{max_attempts}")
            try:
                otp = get_latest_otp_imap(
                    imap_host=IMAP_HOST,
                    username=IMAP_USER,
                    password=IMAP_PASS,
                    email_to=email,
                    timeout_sec=30,
                    subject_filter="Forget Password Token"
                )
                print(f"OTP retrieved: {otp}" if otp else "No OTP found in email")
                
                if otp:
                    break
                    
                if attempt < max_attempts - 1:
                    print(f"Waiting 5 seconds before next attempt...")
                    time.sleep(5)  # Wait before next attempt
                    
            except Exception as e:
                print(f"Error retrieving OTP: {str(e)}")
                if attempt == max_attempts - 1:
                    raise
                print("Retrying...")
                time.sleep(5)
        
        if not otp:
            pytest.fail("Failed to retrieve OTP after multiple attempts")
        
        # 5. Enter OTP and verify
        print(f"Entering OTP: {otp}")
        self.reset_password_page.verify_otp(otp)
        self.reset_password_page.click_verify_button()
        
        # 6. Wait for new password fields to be visible
        print("Waiting for new password fields...")
        self.reset_password_page.new_password_input.wait_for(state="visible", timeout=10000)
        
        # 7. Set new password
        print(f"Setting new password: {self.new_password}")
        self.reset_password_page.set_new_password(
            new_password=self.new_password,
            confirm_password=self.new_password
        )
        
        # 8. Submit the new password
        print("Submitting new password...")
        self.reset_password_page.submit_new_password()
        
        # 9. Verify success message
        print("Verifying password reset success message...")
        expect(self.reset_password_page.reset_success_message).to_be_visible(timeout=10000)
        
        print("Test completed successfully!")
        
        # Update the credentials for subsequent tests if needed
        CREDENTIALS["DEFAULT"]["password"] = self.new_password
        
    def test_reset_password_invalid_email(self):
        """Test reset password with an invalid email format shows appropriate error message."""
        print("Starting test_reset_password_invalid_email...")
        
        # 1. Request reset code with invalid email
        invalid_email = "invalid-email-format"
        print(f"Requesting password reset code for invalid email: {invalid_email}")
        
        # Request reset code with invalid email
        self.reset_password_page.request_reset_code(invalid_email)
        
        # 2. Verify error message is displayed
        print("Verifying error message...")
        error_message = self.reset_password_page.page.locator(
            "p.text-sm.font-medium:has-text('Failed to send password reset code.')"
        )
        
        # Wait for the error message to be visible with a timeout
        expect(error_message).to_be_visible(timeout=10000)
        
        # Additional verification that the error message has the exact text
        expect(error_message).to_have_text("Failed to send password reset code.")
        
        print("Test completed successfully!")

    def test_password_mismatch(self):
        """Test that password mismatch shows appropriate error."""
        print("Starting test_password_mismatch...")
        
        # Request reset link
        self.reset_password_page.request_reset_link(self.test_user["email"])
        
        # Simulate OTP entry
        test_otp = "123456"
        self.reset_password_page.verify_otp(test_otp)
        
        # Set mismatched passwords
        print("Setting mismatched passwords...")
        self.reset_password_page.new_password_input.fill(self.test_user["new_password"])
        self.reset_password_page.confirm_password_input.fill("DifferentPassword123!")
        self.reset_password_page.reset_password_btn.click()
        
        # Verify error message
        print("Verifying error message...")
        expect(self.reset_password_page.error_message).to_be_visible()
        expect(self.reset_password_page.error_message).to_contain_text("Passwords do not match")
        
        print("Test completed successfully!")
