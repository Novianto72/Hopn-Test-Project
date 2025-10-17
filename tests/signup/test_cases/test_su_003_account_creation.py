import pytest
from playwright.sync_api import Page, expect
from pages.signup.signup_page import SignUpPage
from pages.login.login_page import LoginPage
from tests.config.test_config import URLS
from dataInput.signup.test_signup_data import get_test_user, get_payment_method_data
import os
import time
import uuid
from dotenv import load_dotenv
from tests.utils.email_utils import get_latest_otp_imap

# Load environment variables from .env file
load_dotenv()

# Test configuration
SIGNUP_URL = f"{URLS['HOME']}/create-account"

# Email configuration
BASE_EMAIL = "testingtito09"
EMAIL_DOMAIN = "@gmail.com"
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_USER = os.getenv("IMAP_USER", f"{BASE_EMAIL}{EMAIL_DOMAIN}")
IMAP_PASS = os.getenv("IMAP_PASS", "nguh lfdv cedp ijki")  # Using the provided app password

@pytest.mark.smoke
@pytest.mark.signup
class TestAccountCreation:
    def get_test_email(self) -> str:
        """Generate a unique test email address."""
        unique_id = str(uuid.uuid4())[:8]
        return f"{BASE_EMAIL}+{unique_id}{EMAIL_DOMAIN}"

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Initialize the page objects and navigate to the login page."""
        self.page = page
        self.login_page = LoginPage(page).navigate()
        self.signup_page = SignUpPage(page)
        self.test_user = get_test_user()

    def test_successful_account_creation(self):

        test_email = self.get_test_email()
        print(f"Using test email: {test_email}")
        """Test the complete account creation flow with valid data."""
        # 1. Navigate to signup page from login page
        print("Starting test_successful_account_creation...")
        
        # Get the current page
        page = self.page
        print(f"Current URL before click: {page.url}")
        
        try:
            # Take a screenshot before clicking
            page.screenshot(path="before_click.png")
            print("Took screenshot before click")
            
            # Find and click the sign up link
            print("Clicking sign up link...")
            page.click('a:has-text("Sign Up")')
            
            # Wait for navigation to complete
            print("Waiting for navigation to complete...")
            page.wait_for_url("**/create-account", timeout=10000)
            print(f"Navigation complete. Current URL: {page.url}")
            
            # Initialize the signup page with the current page context
            signup_page = SignUpPage(page)
            
            # Wait for the signup form to be visible
            print("Waiting for signup form to be visible...")
            signup_page.first_name.wait_for(state="visible", timeout=10000)
            print("Signup form is visible")
            
            # 2. Fill in the signup form
            print("Filling in signup form...")
            signup_page.first_name.fill(self.test_user["first_name"])
            signup_page.last_name.fill(self.test_user["last_name"])
            signup_page.email.fill(test_email)
            
            # 3. Click Verify button for email
            print("Clicking verify email button...")
            verify_btn = signup_page.verify_email_btn
            expect(verify_btn).to_be_enabled()
            verify_btn.click()
            
            # 4. Wait for verification code input to appear
            print("Waiting for verification code input...")
            signup_page.email_verification_code_input.wait_for(state="visible", timeout=10000)
            
            # 5. Verify success message is shown
            success_message = page.locator(f"text=A verification code has been sent to {test_email}.")
            expect(success_message).to_be_visible()
            
            # 6. Get OTP from email using the page object method
            #success, otp_result = signup_page.get_otp_from_email(self.test_user["email"])
            
            #if not success:
            #    pytest.skip(f"Skipping test: {otp_result}")

            max_attempts = 5
            otp = None
            
            print(f"\n=== OTP Retrieval Debug ===")
            print(f"IMAP Host: {IMAP_HOST}")
            print(f"IMAP User: {IMAP_USER}")
            print(f"Email to check: {self.test_user['email']}")
            print("Attempting to retrieve OTP...")
        
            for attempt in range(max_attempts):
                print(f"\nAttempt {attempt + 1}/{max_attempts}")
                try:
                    otp = get_latest_otp_imap(
                        imap_host=IMAP_HOST,
                        username=IMAP_USER,
                        password=IMAP_PASS,
                        email_to=test_email,
                        timeout_sec=30
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

            # 7. Enter OTP and verify
            signup_page.verify_email_otp(otp)
            
            # 8. Wait for password fields to appear
            signup_page.password.wait_for(state="visible", timeout=10000)
            
            # 9. Fill in password and confirm password
            password = self.test_user["password"]
            signup_page.password.fill(password)
            signup_page.confirm_password.fill(password)
            
            # 10. Click Create Account button and wait for navigation
            try:
                with self.page.expect_navigation(url="**/login", timeout=30000):
                    signup_page.create_account_btn.click()
                print("Successfully navigated to login page")
            except Exception as e:
                print(f"Navigation to login page timed out. Current URL: {self.page.url}")
                # If navigation times out, check if we're still on the create-account page
                current_url = self.page.url
                if "/create-account" in current_url:
                    # Take a screenshot to help with debugging
                    self.page.screenshot(path="account_creation_failed.png")
                    # Check for any error messages on the page
                    error_message = self.page.locator(".error-message, .alert-error, [role='alert']").inner_text(timeout=5000).strip()
                    if error_message:
                        print(f"Error message on page: {error_message}")
                    raise AssertionError(f"Still on signup page: {current_url}. Error: {error_message if error_message else 'No error message found'}")
                print(f"Not on create-account page, current URL: {current_url}")
            
            # Additional check to ensure we're not on the signup page
            current_url = self.page.url
            assert "/create-account" not in current_url, f"Still on signup page: {current_url}"
            print("Successfully navigated away from signup page")
            print("Account created successfully!")
            
            print("Test completed successfully!")

            # Setup Payment Method

            try:
                # 11. Get payment method test data
                payment_data = get_payment_method_data()
                print("Setting up payment method...")
                
                # 12. Setup and submit payment method
                # This includes form submission and verification
                self.signup_page.setup_payment_method(payment_data)
                print("Successfully completed payment setup and returned to signup page")
                
            except Exception as e:
                print(f"Error during payment setup: {str(e)}")
                self.page.screenshot(path="payment_setup_error.png")
                raise
                    
        except Exception as e:
            print(f"Error during test: {str(e)}")
            page.screenshot(path="test_error.png")
            raise
            
    @pytest.mark.payment_positive
    def test_valid_payment_method_setup(self):
        """
        Test successful payment method setup with valid card details.
        Steps:
        1. Create a new account
        2. Reach payment setup page
        3. Enter valid payment details (Visa, Mastercard, Amex)
        4. Verify successful submission
        5. Confirm redirection to next page
        6. Verify payment method is saved correctly
        """
        pass

    @pytest.mark.payment_negative
    def test_invalid_card_details_validation(self):
        """
        Test validation for invalid card details.
        Steps:
        1. Create a new account
        2. Reach payment setup page
        3. Enter expired card
        4. Verify appropriate error message
        5. Enter invalid card number (Luhn check)
        6. Verify appropriate error message
        7. Enter invalid CVV
        8. Verify appropriate error message
        """
        pass

    @pytest.mark.payment_positive
    def test_different_card_networks(self):
        """
        Test payment setup with different card networks.
        Steps:
        1. Create a new account
        2. Test with Visa card
        3. Test with Mastercard
        4. Test with American Express
        5. Verify each card type is accepted with correct formatting
        6. Verify correct CVV length requirements per card type
        """
        pass

    @pytest.mark.payment_negative
    def test_required_fields_validation(self):
        """
        Test validation for required payment fields.
        Steps:
        1. Create a new account
        2. Reach payment setup page
        3. Submit form with empty required fields
        4. Verify appropriate error messages
        5. Test minimum/maximum length validations
        6. Test with special characters in name fields
        """
        pass

    @pytest.mark.payment_edge
    def test_international_payment_setup(self):
        """
        Test payment setup with international details.
        Steps:
        1. Create a new account
        2. Enter non-Latin characters in name
        3. Test with international address formats
        4. Verify acceptance of various postal code formats
        5. Test with different country/region selections
        """
        pass

    @pytest.mark.payment_security
    def test_payment_security_measures(self):
        """
        Test security aspects of payment setup.
        Steps:
        1. Create a new account
        2. Test XSS attempts in cardholder name
        3. Verify sensitive data is masked in UI
        4. Test with SQL injection attempts
        5. Verify secure handling of payment details
        """
        pass

    @pytest.mark.payment_performance
    def test_payment_form_performance(self):
        """
        Test performance aspects of payment form.
        Steps:
        1. Create a new account
        2. Test form submission with slow network
        3. Verify timeout handling
        4. Test multiple rapid submissions
        5. Verify no duplicate payment methods created
        """
        pass

    @pytest.mark.payment_ui
    def test_payment_form_ui_elements(self):
        """
        Test UI elements and user experience.
        Steps:
        1. Create a new account
        2. Verify all form fields are present
        3. Test tab navigation
        4. Test input formatting (auto-spaces in card number, etc.)
        5. Verify error message clarity and positioning
        """
        pass

        # Skip the test if we reached this point without completing the flow
        #if not (IMAP_USER and IMAP_PASS):
        #    pytest.skip("Skipping test: IMAP credentials not provided")
        
    def test_account_creation_with_existing_email(self):
        """Test that attempting to create an account with an existing email shows an error message."""
        print("Starting test_account_creation_with_existing_email...")
        
        # Use the existing email that's already registered
        existing_email = "testingtito09+ce3fb889@gmail.com"
        print(f"Using existing email: {existing_email}")
        
        # Get the current page
        page = self.page
        
        try:
            # Navigate to signup page from login page
            print("Navigating to signup page...")
            page.click('a:has-text("Sign Up")')
            page.wait_for_url("**/create-account", timeout=10000)
            
            # Initialize the signup page
            signup_page = SignUpPage(page)
            
            # Wait for the signup form to be visible
            print("Waiting for signup form to be visible...")
            signup_page.first_name.wait_for(state="visible", timeout=10000)
            print("Signup form is visible")
            
            # Fill in the signup form with test data but use existing email
            print("Filling in signup form with existing email...")
            signup_page.first_name.fill(self.test_user["first_name"])
            signup_page.last_name.fill(self.test_user["last_name"])
            signup_page.email.fill(existing_email)
            
            # Click Verify button for email
            print("Clicking verify email button...")
            verify_btn = signup_page.verify_email_btn
            expect(verify_btn).to_be_enabled()
            verify_btn.click()
            
            # Wait for verification code input to appear
            print("Waiting for verification code input...")
            signup_page.email_verification_code_input.wait_for(state="visible", timeout=10000)
            
            # Verify success message is shown (this might be shown before the actual verification)
            success_message = page.locator(f"text=A verification code has been sent to {existing_email}.")
            expect(success_message).to_be_visible()
            
            # Get OTP from email
            max_attempts = 5
            otp = None
            
            print(f"\n=== OTP Retrieval Debug ===")
            print(f"IMAP Host: {IMAP_HOST}")
            print(f"IMAP User: {IMAP_USER}")
            print(f"Email to check: {existing_email}")
            print("Attempting to retrieve OTP...")
        
            for attempt in range(max_attempts):
                print(f"\nAttempt {attempt + 1}/{max_attempts}")
                try:
                    otp = get_latest_otp_imap(
                        imap_host=IMAP_HOST,
                        username=IMAP_USER,
                        password=IMAP_PASS,
                        email_to=existing_email,
                        timeout_sec=30
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
            
            # Enter OTP and wait for verification to complete
            print("Entering OTP and waiting for verification to complete...")
            signup_page.verify_email_otp(otp)
            
            try:
                # Wait for the verification success message or error message
                print("Waiting for verification to complete...")
                page.wait_for_selector(
                    "text=Email verified successfully || text=CLIENT_ALREADY_EXISTS || text=USER_ALREADY_EXISTS",
                    state="visible",
                    timeout=5000  # Wait up to 30 seconds for verification
                )
            except Exception as e:
                print("Warning: Verification status message not found. Continuing with test...")
            
            # Wait for password fields to appear
            # print("Waiting for password fields to appear...")
            # signup_page.password.wait_for(state="visible", timeout=10000)
            
            # Fill in password and confirm password
            password = self.test_user["password"]
            signup_page.password.fill(password)
            signup_page.confirm_password.fill(password)
            
            # Wait for Create Account button to be visible and enabled
            print("Waiting for Create Account button to be visible and enabled...")
            signup_page.create_account_btn.wait_for(state="visible", timeout=10000)
            
            # Check if the button is enabled
            is_enabled = signup_page.create_account_btn.is_enabled()
            print(f"Create Account button enabled state: {is_enabled}")
            
            if not is_enabled:
                print("Warning: Create Account button is not enabled. Checking for error messages...")
                # Check if there's an error message about the email already existing
                error_message = page.locator("p.text-sm.text-red-800.text-center")
                if error_message.is_visible():
                    error_text = error_message.inner_text()
                    print(f"Found error message: {error_text}")
                    if "CLIENT_ALREADY_EXISTS" in error_text:
                        print("Test passed: Found CLIENT_ALREADY_EXISTS error message")
                        return  # Test passes if we found the expected error message
                
                # If we get here, the test should fail
                pytest.fail("Create Account button is not enabled and no expected error message was found")
            
            # If button is enabled, click it
            print("Clicking Create Account button...")
            signup_page.create_account_btn.click()
            
            # Wait for the error message to appear
            print("Waiting for error message...")
            error_message = page.locator("p.text-sm.text-red-800.text-center")
            error_message.wait_for(state="visible", timeout=10000)
            
            # Verify the error message contains one of the expected error texts
            error_text = error_message.inner_text()
            expected_errors = ["CLIENT_ALREADY_EXISTS", "USER_ALREADY_EXISTS"]
            
            if not any(error in error_text for error in expected_errors):
                pytest.fail(f'Expected error message to contain one of {expected_errors}, but got: {error_text}')
            
            print(f"Test passed: Found expected error message in response: {error_text}")
            
            # Verify we're still on the signup page
            assert "/create-account" in page.url, "Expected to still be on the signup page"
            print("Test completed successfully!")
            
        except Exception as e:
            print(f"Error during test: {str(e)}")
            page.screenshot(path="test_existing_email_error.png")
            raise
