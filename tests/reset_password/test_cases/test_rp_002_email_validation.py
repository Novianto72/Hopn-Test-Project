import time
import pytest
from playwright.sync_api import Page, expect
from pages.reset_password.reset_password_page import ResetPasswordPage
from tests.config.test_config import URLS

class TestResetPasswordEmailValidation:
    """Test cases for email validation in the reset password flow."""
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Initialize the page object and navigate to reset password page."""
        self.page = page
        self.base_url = URLS['HOME']
        self.reset_password_page = ResetPasswordPage(page).navigate_to_reset_password(self.base_url)
        page.wait_for_load_state('networkidle')

    def test_empty_email_disables_send_code_button(self):
        """Test that empty email keeps the Send Code button disabled."""
        # Verify Send Code button is initially disabled
        expect(self.reset_password_page.send_code_btn).to_be_disabled()
        
        # Clear the email input (in case there's a default value)
        self.reset_password_page.email_input.fill("")
        self.reset_password_page.email_input.press("Backspace")  # Ensure it's really empty
        
        # Verify Send Code button remains disabled
        expect(self.reset_password_page.send_code_btn).to_be_disabled()
        
        # Verify no error message is shown
        error_message = self.reset_password_page.page.locator(
            "div.bg-red-50.border-red-200.text-red-700 p.font-medium"
        )
        expect(error_message).to_have_count(0)
    
    @pytest.mark.parametrize("email, expected_error", [
        # Missing @ symbol
        ("userexample.com", "Failed to send password reset code."),
        # Missing domain
        ("user@", "Failed to send password reset code."),
        # Invalid domain format
        ("user@example", "Failed to send password reset code."),
        # Multiple @ symbols
        ("user@@example.com", "Failed to send password reset code."),
        # Spaces in email
        ("user @example.com", "Failed to send password reset code."),
        ("user@ example.com", "Failed to send password reset code."),
        # Special characters
        ("user!@example.com", "Failed to send password reset code."),
    ])
    def test_invalid_email_formats(self, email, expected_error):
        """Test various invalid email formats show appropriate error messages."""
        # Enter invalid email
        self.reset_password_page.email_input.fill(email)
        
        # Verify Send Code button is enabled (since there's some input)
        expect(self.reset_password_page.send_code_btn).to_be_enabled()
        
        # Click Send Code button to trigger validation
        self.reset_password_page.send_code_btn.click()
        
        # Wait for the error message to appear
        time.sleep(2)  # Wait for the error message to be displayed
        
        # Wait for the error message to appear after the loading state
        error_message = self.reset_password_page.page.locator(
            "div.bg-red-50.border-red-200.text-red-700 p.font-medium"
        )
        # Wait for the error message to be visible with a longer timeout
        error_message.wait_for(state="visible", timeout=10000)
        expect(error_message).to_contain_text(expected_error)
        
    @pytest.mark.parametrize("email", [
        "user@example.com",
        "user.name@example.com",
        "user+tag@example.com",
        "user.name+tag@sub.example.co.uk",
        "user@subdomain.example.com",
    ])
    def test_valid_email_enables_button(self, email):
        """Test that valid email formats enable the Send Code button."""
        # Enter valid email
        self.reset_password_page.email_input.fill(email)
        
        # Verify Send Code button is enabled
        expect(self.reset_password_page.send_code_btn).to_be_enabled()

    def test_email_case_insensitivity(self):
        """Test that email input is case insensitive."""
        email = "USER@example.com"
        self.reset_password_page.email_input.fill(email)
        
        # Verify the email is accepted (case should be preserved but not affect validation)
        expect(self.reset_password_page.send_code_btn).to_be_enabled()

    def test_paste_operation(self):
        """Test pasting an email into the field works correctly."""
        # Simulate pasting a valid email with extra spaces
        self.reset_password_page.email_input.fill("  user@example.com  ")
        
        # Verify the email is accepted (should be trimmed)
        expect(self.reset_password_page.send_code_btn).to_be_enabled()
        expect(self.reset_password_page.email_input).to_have_value("user@example.com")

    def test_international_email_support(self):
        """Test support for international email addresses."""
        international_email = "用户@例子.广告"
        self.reset_password_page.email_input.fill(international_email)
        
        # Verify the email is accepted
        expect(self.reset_password_page.send_code_btn).to_be_enabled()
        expect(self.reset_password_page.email_input).to_have_value(international_email)

    def test_clear_field_disables_button(self):
        """Test that clearing the email field disables the Send Code button."""
        # First enter a valid email
        self.reset_password_page.email_input.fill("user@example.com")
        
        # Then clear the field
        self.reset_password_page.email_input.fill("")
        
        # Verify button is disabled
        expect(self.reset_password_page.send_code_btn).to_be_disabled()

    def test_error_message_cleared_on_valid_input(self):
        """Test that error message is cleared when input becomes valid."""
        # First enter invalid email to show error
        self.reset_password_page.email_input.fill("invalid")
        self.reset_password_page.send_code_btn.click()
        
        # Verify error message is shown
        error_message = self.reset_password_page.page.locator("div.bg-red-50.border-red-200.text-red-700")
        expect(error_message).to_be_visible()
        expect(error_message).to_contain_text("Failed to send password reset code.")
        
        # Enter valid email
        self.reset_password_page.email_input.fill("mamado.2000@gmail.com")
        self.reset_password_page.send_code_btn.click()

        time.sleep(3)

        # Verify error message is cleared
        expect(error_message).not_to_be_visible()
        
        # Verify button is enabled
        expect(self.reset_password_page.send_code_btn).to_be_enabled()
