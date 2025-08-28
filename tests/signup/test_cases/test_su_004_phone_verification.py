import pytest
from playwright.sync_api import Page, expect
from dotenv import load_dotenv
from pages.signup.signup_page import SignUpPage
import time


# Load environment variables
load_dotenv()

@pytest.mark.phone_verification
class TestPhoneVerification:
    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Initialize the page object and navigate to signup page."""
        self.signup_page = SignUpPage(page).navigate()
        self.page = page
        
        # Store locators from page object
        self.country_code = self.signup_page.country_code
        self.phone_number = self.signup_page.phone_number
        self.verify_phone_btn = self.signup_page.verify_phone_btn
        self.error_message = page.locator("p.text-red-500")

    def test_verify_button_states(self):
        """Test verify button states with different input combinations."""
        # Initial state - both fields empty
        expect(self.verify_phone_btn).to_be_disabled()
        
        # Only country code filled
        self.country_code.fill("+1")
        expect(self.verify_phone_btn).to_be_disabled()
        
        # Only phone number filled
        self.country_code.fill("")
        self.phone_number.fill("1234567890")
        expect(self.verify_phone_btn).to_be_disabled()
        
        # Both fields filled
        self.country_code.fill("+1")
        expect(self.verify_phone_btn).to_be_enabled()

    @pytest.mark.parametrize("country_code,phone_number,should_succeed,expected_error", [
        ("+1", "1234567890", True, None),  # Valid US number
        ("+1", "123", False, "Failed to send verification code."),  # Too short
        ("+1", "abc", False, "Failed to send verification code."),  # Non-numeric
        ("+1", "!@#$", False, "Failed to send verification code."),  # Special chars
        ("+1", " " * 10, False, "Failed to send verification code."),  # Spaces
    ])
    def test_phone_validation(self, country_code: str, phone_number: str, 
                            should_succeed: bool, expected_error: str):
        """Test phone number validation with various inputs."""
        # Refresh the page before each test case
        self.page.reload()
        
        # Re-initialize the page object after reload
        self.signup_page = SignUpPage(self.page).navigate()
        self.country_code = self.signup_page.country_code
        self.phone_number = self.signup_page.phone_number
        self.verify_phone_btn = self.signup_page.verify_phone_btn
        
        # Fill in the form
        self.country_code.fill(country_code)
        self.phone_number.fill(phone_number)
        
        # Check if we expect this to be a valid form submission
        if country_code and phone_number.strip():
            expect(self.verify_phone_btn).to_be_enabled()
            self.verify_phone_btn.click()
            
            if should_succeed:
                # For successful case, OTP field should appear
                expect(self.signup_page.phone_otp_input_field).to_be_visible(timeout=10000)  # Increased timeout for OTP field
            else:
                # For error cases, verify error message appears
                # The verify button should remain enabled to allow retry
                expect(self.error_message).to_be_visible(timeout=10000)  # Increased timeout for error message
                expect(self.error_message).to_contain_text("Failed to send verification code")
                expect(self.verify_phone_btn).to_be_enabled()
        else:
            # For invalid inputs, the button should remain enabled to allow retry
            expect(self.verify_phone_btn).to_be_enabled()
            self.verify_phone_btn.click()
            
            # Verify error message appears
            expect(self.error_message).to_be_visible(timeout=10000)
            expect(self.error_message).to_contain_text("Failed to send verification code")

    def test_otp_flow(self):
        """Test OTP field appears after phone verification."""
        # Fill phone number and verify
        self.country_code.fill("+1")
        self.phone_number.fill("1234567890")
        self.verify_phone_btn.click()
        
        # Verify OTP input field is visible and enabled
        expect(self.signup_page.phone_otp_input).to_be_visible(timeout=10000)
        expect(self.signup_page.phone_otp_input).to_be_enabled()
        
        # Test that we can input into the OTP field
        test_otp = "123456"
        self.signup_page.phone_otp_input.fill(test_otp)
        
        # Verify the input was successful
        expect(self.signup_page.phone_otp_input).to_have_value(test_otp)

        # Verify Check button is visible and enabled
        expect(self.signup_page.phone_otp_check_button).to_be_visible()
        expect(self.signup_page.phone_otp_check_button).to_be_enabled()

    @pytest.mark.parametrize("invalid_otp, description", [
        ("12345", "5 digits (too short)"),
        ("1234567", "7 digits (too long)"),
        ("abc123", "Contains letters and numbers"),
        ("!@#$%^", "Special characters only"),
        ("      ", "Whitespace only"),
        ("123abc", "Numbers and letters"),
        ("１２３４５６", "Full-width numbers")
    ])
    def test_invalid_otp_scenarios(self, invalid_otp: str, description: str):
        """Test various invalid OTP scenarios and verify error message."""
        # Fill phone number and verify
        self.country_code.fill("+1")
        self.phone_number.fill("1234567890")
        self.verify_phone_btn.click()
        
        # Wait for OTP input field
        expect(self.signup_page.phone_otp_input).to_be_visible(timeout=10000)
        
        # Clear any existing input and enter invalid OTP
        self.signup_page.phone_otp_input.fill("")
        self.signup_page.phone_otp_input.fill(invalid_otp)
        
        # Click the check button
        self.signup_page.phone_otp_check_button.click()
        
        time.sleep(3)

        expect(self.signup_page.phone_otp_error_message).to_be_visible()
