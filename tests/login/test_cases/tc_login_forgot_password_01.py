import pytest
from playwright.sync_api import Page, expect
from pages.login.login_page import LoginPage
from tests.config.test_config import URLS

@pytest.mark.login
class TestLoginForgotPassword:
    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Initialize the page object and navigate to the login page."""
        self.page = page
        self.login_page = LoginPage(page).navigate()

    def test_forgot_password_link_redirection(self):
        """Test that clicking Forgot Password link redirects to the reset password page."""
        print("Starting test_forgot_password_link_redirection...")
        
        # Click the Forgot Password link
        print("Clicking Forgot Password link...")
        current_url = self.login_page.click_forgot_password()
        
        # Verify the URL contains the reset-password path
        print("Verifying URL redirection...")
        assert "reset-password" in current_url.lower(), \
            f"Expected to be redirected to reset password page, but got: {current_url}"
        
        # Verify we're on the expected URL
        expected_url = f"{URLS['HOME']}/reset-password"
        assert current_url == expected_url, \
            f"Expected URL: {expected_url}, but got: {current_url}"
            
        print("Test completed successfully!")

    def test_forgot_password_link_visibility(self):
        """Test that the Forgot Password link is visible and has the correct text."""
        print("Starting test_forgot_password_link_visibility...")
        
        # Verify the Forgot Password link is visible
        print("Verifying Forgot Password link is visible...")
        expect(self.login_page.forgot_password_link).to_be_visible()
        
        # Verify the link text
        print("Verifying link text...")
        link_text = self.login_page.forgot_password_link.inner_text().strip()
        assert link_text == "Forgot password?", \
            f"Expected link text 'Forgot password?', but got: '{link_text}'"
            
        print("Test completed successfully!")
