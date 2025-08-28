from playwright.sync_api import Page, expect
from typing import Optional

class SignUpPage:
    # Locators
    _FIRST_NAME = "input#firstName"
    _LAST_NAME = "input#lastName"
    _EMAIL = "input#email"
    _PHONE_OTP_INPUT = "input#phoneOtp"
    _VERIFY_EMAIL_BTN = '//label[text()="Email"]/../div/button'
    _COUNTRY_CODE = "input#countryCode"
    _PHONE_NUMBER = "input#phoneNumber"
    _VERIFY_PHONE_BTN = '//label[text()="Phone Number"]/../div/div/div/button'
    _PASSWORD = "input#password"
    _CONFIRM_PASSWORD = "input#confirmPassword"
    _CREATE_ACCOUNT_BTN = "button[type='submit']"
    _EMAIL_VERIFICATION_CODE_INPUT = "input#emailOtp"
    _EMAIL_VERIFICATION_CHECK_BTN = '//label[text()="Email Verification Code"]/../div/button[text()="Check"]'
    _PHONE_VERIFICATION_CODE_INPUT = "input#phoneOtp"
    _PHONE_VERIFICATION_CHECK_BTN = '//label[text()="Phone Verification Code"]/../div/button[text()="Check"]'
    _PHONE_OTP_INPUT_FIELD = "input#phoneOtp"
    _PHONE_OTP_CHECK_BUTTON = '//label[text()="Phone Verification Code"]/../div/button[text()="Check"]'
    _PHONE_OTP_ERROR_MESSAGE = 'p.text-sm.text-red-500:has-text("Invalid or expired verification code")'

    def __init__(self, page: Page):
        self.page = page
        self.url = "https://wize-invoice-dev-front.octaprimetech.com/create-account"
        
        # Form fields
        self.first_name = page.locator(self._FIRST_NAME)
        self.last_name = page.locator(self._LAST_NAME)
        self.email = page.locator(self._EMAIL)
        self.verify_email_btn = page.locator(self._VERIFY_EMAIL_BTN)
        self.country_code = page.locator(self._COUNTRY_CODE)
        self.phone_number = page.locator(self._PHONE_NUMBER)
        self.verify_phone_btn = page.locator(self._VERIFY_PHONE_BTN)
        self.password = page.locator(self._PASSWORD)
        self.confirm_password = page.locator(self._CONFIRM_PASSWORD)
        self.create_account_btn = page.locator(self._CREATE_ACCOUNT_BTN)
        self.email_verification_code_input = page.locator(self._EMAIL_VERIFICATION_CODE_INPUT)
        self.email_verification_check_btn = page.locator(self._EMAIL_VERIFICATION_CHECK_BTN)
        self.phone_otp_input_field = page.locator(self._PHONE_OTP_INPUT)
        self.phone_verification_code_input = page.locator(self._PHONE_VERIFICATION_CODE_INPUT)
        self.phone_verification_check_btn = page.locator(self._PHONE_VERIFICATION_CHECK_BTN)
        self.phone_otp_input = page.locator(self._PHONE_OTP_INPUT_FIELD)
        self.phone_otp_check_button = page.locator(self._PHONE_OTP_CHECK_BUTTON)
        self.phone_otp_error_message = page.locator(self._PHONE_OTP_ERROR_MESSAGE)
    
    def navigate(self):
        self.page.goto(self.url)
        return self
    
    def is_loaded(self):
        return all([
            self.first_name.is_visible(),
            self.last_name.is_visible(),
            self.email.is_visible(),
            self.verify_email_btn.is_visible(),
            self.country_code.is_visible(),
            self.phone_number.is_visible(),
            self.verify_phone_btn.is_visible(),
            self.password.is_visible(),
            self.confirm_password.is_visible(),
            self.create_account_btn.is_visible()
        ])
        
    def verify_email_otp(self, otp: str):
        """Enter and submit email OTP verification code"""
        self.email_verification_code_input.fill(otp)
        self.email_verification_check_btn.click()
        
    def verify_phone_otp(self, otp: str):
        """Enter and submit phone OTP verification code"""
        self.phone_verification_code_input.fill(otp)
        self.phone_verification_check_btn.click()
    
    def fill_form(self, first_name: str, last_name: str, email: str, 
                 country_code: str, phone: str, password: str, confirm_password: str):
        self.first_name.fill(first_name)
        self.last_name.fill(last_name)
        self.email.fill(email)
        self.country_code.fill(country_code)
        self.phone_number.fill(phone)
        self.password.fill(password)
        self.confirm_password.fill(confirm_password)
    
    def submit_form(self):
        self.create_account_btn.click()
