import pytest
import time
from playwright.sync_api import Page, expect
from dotenv import load_dotenv
import os
from tests.config.test_config import URLS

load_dotenv()

# Test configuration
BASE_URL = URLS['HOME']
SIGNUP_URL = f"{BASE_URL}/create-account"

@pytest.mark.regression
class TestPasswordValidation:
    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Navigate to the signup page before each test."""
        page.goto(SIGNUP_URL)
        # Wait for the page to load
        page.wait_for_selector("input#email")

    def test_passwords_match(self, page: Page):
        """Test that no error is shown when passwords match."""
        password = "Test@1234"
        
        # Fill in the password fields with matching values
        page.fill("input#password", password)
        page.fill("input#confirmPassword", password)
        
        # Trigger validation by clicking outside the fields
        page.click("body")
        
        # Verify no error message is visible
        error_message = page.locator("p.text-red-800")
        expect(error_message).to_have_count(0)

    def test_passwords_do_not_match(self, page: Page):
        """Test that error is shown when passwords don't match."""
        # Fill in the password fields with different values
        page.fill("input#password", "Test@1234")
        page.fill("input#confirmPassword", "Different@1234")
        
        # Trigger validation by clicking outside the fields
        page.click("body")
        
        # Verify error message is visible and has correct text
        error_message = page.locator("p.text-red-800")
        expect(error_message).to_be_visible()
        expect(error_message).to_have_text("Passwords do not match.")

    @pytest.mark.skip(reason="Required field validation not currently implemented in the UI")
    def test_password_required_validation(self, page: Page):
        """Test that password field shows required validation."""
        # This test is skipped as the UI doesn't currently show validation for empty required fields
        # until the form is submitted
        pass

    @pytest.mark.skip(reason="Required field validation not currently implemented in the UI")
    def test_confirm_password_required_validation(self, page: Page):
        """Test that confirm password field shows required validation."""
        # This test is skipped as the UI doesn't currently show validation for empty required fields
        # until the form is submitted
        pass

    @pytest.mark.skip(reason="Minimum length validation is handled by disabling the Create Account button")
    def test_password_minimum_length(self, page: Page):
        """
        Test that password must be at least 6 characters long.
        Note: Currently, the UI disables the Create Account button for passwords < 6 chars
        instead of showing an error message.
        """
        # This test is skipped as the validation is implemented by disabling the submit button
        # and we can't test the button state without filling all required fields including OTP
        pass
