import pytest
from pages.signup.signup_page import SignUpPage

@pytest.mark.signup
class TestSignUpFormElements:
    @pytest.fixture(autouse=True)
    def setup(self, page):
        self.signup_page = SignUpPage(page).navigate()
    
    def test_all_form_elements_are_visible(self):
        """Verify all form elements are visible on the signup page"""
        # Check all form elements are visible
        assert self.signup_page.is_loaded(), "Not all form elements are visible"
        
        # Additional explicit checks for each element
        assert self.signup_page.first_name.is_visible(), "First Name field is not visible"
        assert self.signup_page.last_name.is_visible(), "Last Name field is not visible"
        assert self.signup_page.email.is_visible(), "Email field is not visible"
        assert self.signup_page.verify_email_btn.is_visible(), "Verify Email button is not visible"
        #assert self.signup_page.country_code.is_visible(), "Country Code field is not visible"
        #assert self.signup_page.phone_number.is_visible(), "Phone Number field is not visible"
        #assert self.signup_page.verify_phone_btn.is_visible(), "Verify Phone button is not visible"
        assert self.signup_page.password.is_visible(), "Password field is not visible"
        assert self.signup_page.confirm_password.is_visible(), "Confirm Password field is not visible"
        assert self.signup_page.create_account_btn.is_visible(), "Create Account button is not visible"
    
    def test_form_field_placeholders(self):
        """Verify all form fields have the correct placeholder text"""
        assert self.signup_page.first_name.get_attribute("placeholder") == "John", "Incorrect placeholder for First Name"
        assert self.signup_page.last_name.get_attribute("placeholder") == "Doe", "Incorrect placeholder for Last Name"
        assert self.signup_page.email.get_attribute("placeholder") == "name@example.com", "Incorrect placeholder for Email"
        #assert self.signup_page.country_code.get_attribute("placeholder") == "+1", "Incorrect placeholder for Country Code"
        #assert self.signup_page.phone_number.get_attribute("placeholder") == "234 567 890", "Incorrect placeholder for Phone Number"
        # Check for aria-label or other attributes since password fields might not use placeholders for security
        assert self.signup_page.password.get_attribute("type") == "password", "Password field should be of type password"
        assert self.signup_page.confirm_password.get_attribute("type") == "password", "Confirm Password field should be of type password"
    
    def test_verify_buttons_initial_state(self):
        """Verify that verify buttons are initially disabled"""
        assert not self.signup_page.verify_email_btn.is_enabled(), "Verify Email button should be disabled initially"
        #assert not self.signup_page.verify_phone_btn.is_enabled(), "Verify Phone button should be disabled initially"
        assert not self.signup_page.create_account_btn.is_enabled(), "Create Account button should be disabled initially"
    
    def test_login_button_redirect(self, page):
        """Verify that clicking the login button redirects to the login page"""
        # Find and click the login link
        login_link = page.locator('a:has-text("Login")')
        assert login_link.is_visible(), "Login link is not visible"
        
        # Click the login link and wait for navigation
        with page.expect_navigation() as nav_info:
            login_link.click()
        
        # Verify the URL after navigation
        from tests.config.test_config import URLS
        assert page.url == URLS["LOGIN"], \
            f"Expected to be redirected to login page, but got {page.url}"
