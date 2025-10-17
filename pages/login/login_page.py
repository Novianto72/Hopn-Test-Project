from playwright.sync_api import Page, expect

class LoginPage:
    # Locators
    _SIGN_UP_LINK = r'a.text-sm.font-medium.text-\[\#11A193\]:has-text("Sign Up")'
    _EMAIL_INPUT = "input#email"
    _PASSWORD_INPUT = "input#password"
    _LOGIN_BUTTON = "button[type='submit']"
    _FORGOT_PASSWORD_LINK = "a:has-text('Forgot Password')"
    _ERROR_MESSAGE = ".text-red-500"

    def __init__(self, page: Page):
        self.page = page
        self.url = "https://wize-invoice-dev-front.octaprimetech.com/login"
        
        # Page elements
        self._sign_up_link_locator = self._SIGN_UP_LINK
        self.email_input = page.locator(self._EMAIL_INPUT)
        self.password_input = page.locator(self._PASSWORD_INPUT)
        self.login_button = page.locator(self._LOGIN_BUTTON)
        self.forgot_password_link = page.locator(self._FORGOT_PASSWORD_LINK)
        self.error_message = page.locator(self._ERROR_MESSAGE)
        
    @property
    def sign_up_link(self):
        """Get the sign up link locator."""
        return self.page.locator(self._sign_up_link_locator)
    
    def navigate(self):
        """Navigate to the login page."""
        self.page.goto(self.url)
        return self
    
    def click_sign_up_link(self):
        """Click the Sign Up link to navigate to the signup page."""
        self.sign_up_link.click()
        return self
    
    def login(self, email: str, password: str):
        """Perform login with the given credentials."""
        self.email_input.fill(email)
        self.password_input.fill(password)
        self.login_button.click()
        return self
        
    def click_forgot_password(self):
        """Click the Forgot Password link and return the current page URL."""
        self.forgot_password_link.click()
        self.page.wait_for_load_state('networkidle')
        return self.page.url
